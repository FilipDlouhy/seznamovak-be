from rest_framework import serializers


class FacultyResponseSerializer(serializers.Serializer):
    """A faculty in the public overview."""

    id = serializers.IntegerField()
    faculty_name = serializers.CharField()
    faculty_abbrev = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
