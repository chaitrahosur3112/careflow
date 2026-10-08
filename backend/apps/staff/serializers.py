from rest_framework import serializers

from .models import StaffShift


class StaffShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffShift
        fields = ["id", "staff_member", "department", "shift_start", "shift_end", "is_on_duty"]
        read_only_fields = ["id"]
