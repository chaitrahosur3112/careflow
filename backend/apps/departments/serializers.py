from rest_framework import serializers

from .models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    bed_occupancy_pct = serializers.ReadOnlyField()
    current_queue_length = serializers.ReadOnlyField()
    staff_on_duty_count = serializers.ReadOnlyField()
    average_wait_time_minutes = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = [
            "id", "name", "total_beds", "occupied_beds", "is_active",
            "bed_occupancy_pct", "current_queue_length", "staff_on_duty_count",
            "average_wait_time_minutes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DepartmentStatsSerializer(serializers.Serializer):
    """Lightweight read-only shape for /departments/:id/stats."""

    department_id = serializers.UUIDField(source="id")
    name = serializers.CharField()
    total_beds = serializers.IntegerField()
    occupied_beds = serializers.IntegerField()
    bed_occupancy_pct = serializers.FloatField()
    current_queue_length = serializers.IntegerField()
    staff_on_duty_count = serializers.IntegerField()
    average_wait_time_minutes = serializers.FloatField()
