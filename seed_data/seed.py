"""
CareFlow demo seed script.

Run from the backend container/venv (needs Django settings on the
path):

    cd backend
    python ../seed_data/seed.py

Creates:
  - 4 departments (Emergency, Cardiology, Pediatrics, Orthopedics)
  - 1 admin, 2 doctors, 3 nurses, 1 hospital administrator
  - ~40 patients spread across waiting / in-treatment / discharged,
    with QueueEvent audit records for each transition
  - A handful of staff shifts, some on-duty right now

All data is synthetic — no real names, no real patient information.
Safe to re-run: it clears previously seeded demo rows first (identified
by a "(seed)" marker in the username) rather than truncating real data.
"""
import os
import random
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careflow_project.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.alerts.models import Alert, AlertSeverity, AlertType  # noqa: E402
from apps.departments.models import Department  # noqa: E402
from apps.patients.models import Patient, PatientStatus, QueueEvent, QueueEventType, TriageLevel  # noqa: E402
from apps.predictions.models import Prediction, PredictionMetric  # noqa: E402
from apps.staff.models import StaffShift  # noqa: E402

User = get_user_model()

DEPARTMENTS = [
    {"name": "Emergency", "total_beds": 20, "occupied_beds": 14},
    {"name": "Cardiology", "total_beds": 15, "occupied_beds": 6},
    {"name": "Pediatrics", "total_beds": 12, "occupied_beds": 9},
    {"name": "Orthopedics", "total_beds": 10, "occupied_beds": 3},
]

TRIAGE_WEIGHTS = [(TriageLevel.P1_CRITICAL, 0.15), (TriageLevel.P2_URGENT, 0.45), (TriageLevel.P3_STANDARD, 0.40)]


def weighted_triage():
    return random.choices([t for t, _ in TRIAGE_WEIGHTS], weights=[w for _, w in TRIAGE_WEIGHTS])[0]


def seed_departments():
    depts = {}
    for d in DEPARTMENTS:
        dept, _ = Department.objects.update_or_create(name=d["name"], defaults=d)
        depts[d["name"]] = dept
    print(f"Departments ready: {list(depts.keys())}")
    return depts


def seed_users(depts):
    User.objects.filter(username__endswith="(seed)").delete()

    admin = User.objects.create_user(
        username="admin(seed)", email="admin.seed@careflow.demo", password="CareFlow!2026",
        role="ADMIN", first_name="Asha", last_name="Rao",
    )

    doctors = [
        User.objects.create_user(
            username=f"dr.{n.lower()}(seed)", email=f"{n.lower()}.seed@careflow.demo", password="CareFlow!2026",
            role="DOCTOR", first_name=n, last_name="Menon", department=depts[dept_name],
        )
        for n, dept_name in [("Vikram", "Emergency"), ("Priya", "Cardiology")]
    ]

    nurses = [
        User.objects.create_user(
            username=f"nurse.{n.lower()}(seed)", email=f"{n.lower()}.seed@careflow.demo", password="CareFlow!2026",
            role="NURSE", first_name=n, last_name="Kumar", department=depts[dept_name],
        )
        for n, dept_name in [("Divya", "Emergency"), ("Farah", "Pediatrics"), ("Ganesh", "Orthopedics")]
    ]

    hospital_admin = User.objects.create_user(
        username="hospitaladmin(seed)", email="hospitaladmin.seed@careflow.demo", password="CareFlow!2026",
        role="HOSPITAL_ADMINISTRATOR", first_name="Neha", last_name="Iyer",
    )

    print(f"Users seeded: 1 admin, {len(doctors)} doctors, {len(nurses)} nurses, 1 hospital administrator")
    print("All seed accounts use password: CareFlow!2026")
    return admin, doctors, nurses, hospital_admin


def seed_shifts(depts, doctors, nurses):
    now = timezone.now()
    for staff_member in doctors + nurses:
        StaffShift.objects.create(
            staff_member=staff_member,
            department=staff_member.department,
            shift_start=now - timedelta(hours=2),
            shift_end=now + timedelta(hours=6),
            is_on_duty=True,
        )
    print(f"Shifts seeded for {len(doctors) + len(nurses)} staff members (all currently on duty)")


def seed_patients(depts, nurses, admin):
    # Filtering by assigned_nurse breaks on rerun: seed_users() deletes and
    # recreates the nurse accounts first, which SETs NULL on assigned_nurse
    # for the patients from the previous run, so they'd never match and
    # the seed data would silently double each run. Department is stable
    # across reruns, so clear by department instead.
    Patient.objects.filter(department__in=depts.values()).delete()
    now = timezone.now()
    created = 0

    for dept_name, dept in depts.items():
        dept_nurses = [n for n in nurses if n.department_id == dept.id] or [admin]
        patient_count = random.randint(6, 12)
        for _ in range(patient_count):
            status = random.choices(
                [PatientStatus.WAITING, PatientStatus.IN_TREATMENT, PatientStatus.DISCHARGED],
                weights=[0.4, 0.3, 0.3],
            )[0]
            intake_offset = timedelta(minutes=random.randint(5, 240))
            nurse = random.choice(dept_nurses)

            patient = Patient.objects.create(
                triage_level=weighted_triage(),
                department=dept,
                status=status,
                assigned_nurse=nurse,
            )
            # intake_time is auto_now_add — backdate it directly for realistic demo data
            patient.intake_time = now - intake_offset
            if status == PatientStatus.DISCHARGED:
                patient.discharge_time = patient.intake_time + timedelta(minutes=random.randint(20, 120))
            patient.save(update_fields=["intake_time", "discharge_time"])

            QueueEvent.objects.create(patient=patient, event_type=QueueEventType.INTAKE, performed_by=nurse, timestamp=patient.intake_time)
            if status != PatientStatus.WAITING:
                QueueEvent.objects.create(
                    patient=patient, event_type=QueueEventType.STATUS_CHANGE, performed_by=nurse,
                    notes=f"status -> {status}",
                )
            if status == PatientStatus.DISCHARGED:
                QueueEvent.objects.create(
                    patient=patient, event_type=QueueEventType.DISCHARGE, performed_by=nurse,
                    timestamp=patient.discharge_time,
                )
            created += 1

    print(f"Patients seeded: {created} across {len(depts)} departments")


def seed_predictions(depts):
    Prediction.objects.filter(department__in=depts.values()).delete()
    now = timezone.now()
    created = 0
    for dept_name, dept in depts.items():
        # Historical wait-time predictions with actual outcomes for analytics MAE/RMSE
        for _ in range(12):
            pred_val = round(random.uniform(15.0, 50.0), 1)
            actual_val = round(max(5.0, pred_val + random.uniform(-4.0, 4.0)), 1)
            p = Prediction.objects.create(
                department=dept,
                metric=PredictionMetric.WAIT_TIME,
                predicted_value=pred_val,
                actual_value=actual_val,
                model_version="v1",
            )
            p.predicted_at = now - timedelta(hours=random.randint(2, 72))
            p.save(update_fields=["predicted_at"])
            created += 1

        # Historical overcrowding-risk predictions with actual outcomes
        for _ in range(12):
            pred_risk = round(random.uniform(40.0, 95.0), 1)
            actual_risk = round(max(10.0, min(100.0, pred_risk + random.uniform(-5.0, 5.0))), 1)
            p = Prediction.objects.create(
                department=dept,
                metric=PredictionMetric.OVERCROWDING_RISK,
                predicted_value=pred_risk,
                actual_value=actual_risk,
                model_version="v1",
            )
            p.predicted_at = now - timedelta(hours=random.randint(2, 72))
            p.save(update_fields=["predicted_at"])
            created += 1

    print(f"Predictions seeded: {created} historical records for accuracy validation")


def seed_alerts(depts, admin):
    Alert.objects.filter(department__in=depts.values()).delete()
    now = timezone.now()
    alerts_data = [
        {
            "department": depts["Emergency"],
            "alert_type": AlertType.OVERCROWDING,
            "severity": AlertSeverity.RED,
            "message": "Emergency at 95% bed occupancy — critical.",
            "acknowledged_at": None,
            "acknowledged_by": None,
            "offset_hours": 1,
        },
        {
            "department": depts["Pediatrics"],
            "alert_type": AlertType.OVERCROWDING,
            "severity": AlertSeverity.AMBER,
            "message": "Pediatrics at 82% bed occupancy — approaching capacity.",
            "acknowledged_at": None,
            "acknowledged_by": None,
            "offset_hours": 2,
        },
        {
            "department": depts["Emergency"],
            "alert_type": AlertType.LONG_WAIT,
            "severity": AlertSeverity.AMBER,
            "message": "Patient wait time exceeded 60 min threshold in Emergency.",
            "acknowledged_at": None,
            "acknowledged_by": None,
            "offset_hours": 3,
        },
        {
            "department": depts["Cardiology"],
            "alert_type": AlertType.OVERCROWDING,
            "severity": AlertSeverity.AMBER,
            "message": "Cardiology approached capacity (resolved).",
            "acknowledged_at": now - timedelta(minutes=45),
            "acknowledged_by": admin,
            "offset_hours": 4,
        },
    ]

    for a in alerts_data:
        offset = a.pop("offset_hours")
        alert = Alert.objects.create(**a)
        alert.created_at = now - timedelta(hours=offset)
        alert.save(update_fields=["created_at"])

    print(f"Alerts seeded: {len(alerts_data)} alerts (both active and acknowledged)")


def main():
    random.seed(42)  # reproducible demo data
    depts = seed_departments()
    admin, doctors, nurses, hospital_admin = seed_users(depts)
    seed_shifts(depts, doctors, nurses)
    seed_patients(depts, nurses, admin)
    seed_predictions(depts)
    seed_alerts(depts, admin)
    print("\nDemo login (Admin): admin.seed@careflow.demo / CareFlow!2026")
    print("Demo login (Doctor): vikram.seed@careflow.demo / CareFlow!2026")
    print("Demo login (Nurse): divya.seed@careflow.demo / CareFlow!2026")
    print("Demo login (Hospital Administrator): hospitaladmin.seed@careflow.demo / CareFlow!2026")
    print("Kiosk view needs no login: /kiosk")


if __name__ == "__main__":
    main()
