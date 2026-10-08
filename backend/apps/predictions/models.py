import uuid

from django.db import models


class PredictionMetric(models.TextChoices):
    WAIT_TIME = "wait_time", "Wait Time (minutes)"
    OVERCROWDING_RISK = "overcrowding_risk", "Overcrowding Risk (0-100)"


class Prediction(models.Model):
    """
    Every call to the FastAPI ML service is logged here so the Analytics
    module can compare predicted_value vs actual_value later (model accuracy).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        "departments.Department", on_delete=models.CASCADE, related_name="predictions"
    )
    predicted_at = models.DateTimeField(auto_now_add=True)
    metric = models.CharField(max_length=32, choices=PredictionMetric.choices)
    predicted_value = models.FloatField()
    actual_value = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=32, default="v1")

    class Meta:
        ordering = ["-predicted_at"]
        indexes = [models.Index(fields=["department", "metric"])]

    def __str__(self):
        return f"{self.metric} pred={self.predicted_value} actual={self.actual_value}"
