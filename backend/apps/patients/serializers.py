from rest_framework import serializers

from .models import Patient, QueueEvent


class PatientSerializer(serializers.ModelSerializer):
    time_in_system_minutes = serializers.ReadOnlyField()

    class Meta:
        model = Patient
        fields = [
            "id", "triage_level", "department", "status", "intake_time",
            "discharge_time", "assigned_nurse", "time_in_system_minutes",
        ]
        read_only_fields = ["id", "intake_time"]


class PatientIntakeSerializer(serializers.ModelSerializer):
    """POST /patients/intake — nurse/triage entry. No name/PII fields exist to submit."""

    class Meta:
        model = Patient
        fields = ["id", "triage_level", "department", "assigned_nurse"]
        read_only_fields = ["id"]


class PatientStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["status"]


class QueueEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueEvent
        fields = ["id", "patient", "event_type", "timestamp", "performed_by", "notes"]
        read_only_fields = ["id", "timestamp"]


class KioskWaitTimeSerializer(serializers.Serializer):
    """
    Public kiosk shape — department name + estimated wait ONLY.
    Never includes patient IDs, counts, or any patient-level field.
    """

    department_name = serializers.CharField()
    estimated_wait_minutes = serializers.FloatField()
    load_level = serializers.CharField()  # "low" | "medium" | "high"
