from rest_framework import serializers

from .models import Prediction


class WaitTimeRequestSerializer(serializers.Serializer):
    department_id = serializers.UUIDField()
    current_queue_length = serializers.IntegerField()
    triage_level = serializers.ChoiceField(choices=["P1", "P2", "P3"])
    staff_on_duty = serializers.IntegerField()
    time_of_day = serializers.IntegerField(min_value=0, max_value=23)
    day_of_week = serializers.IntegerField(min_value=0, max_value=6)


class OvercrowdingRiskRequestSerializer(serializers.Serializer):
    department_id = serializers.UUIDField()
    admission_rate_last_1h = serializers.FloatField()
    bed_occupancy_pct = serializers.FloatField()
    hour_of_day = serializers.IntegerField(min_value=0, max_value=23)


class StaffingRecommendationRequestSerializer(serializers.Serializer):
    department_id = serializers.UUIDField()
    current_load = serializers.FloatField(
        help_text="Current patient queue length (count), not a percentage — matches Department.current_queue_length."
    )
    staff_on_duty = serializers.IntegerField()
    predicted_risk = serializers.FloatField()


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ["id", "department", "predicted_at", "metric", "predicted_value", "actual_value", "model_version"]
        read_only_fields = ["id", "predicted_at"]
