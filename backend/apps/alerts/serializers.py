from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "department", "department_name", "alert_type", "severity",
            "message", "created_at", "acknowledged_by", "acknowledged_at",
        ]
        read_only_fields = ["id", "created_at"]
