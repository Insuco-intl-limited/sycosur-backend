from rest_framework import serializers

from core_apps.projects.models import Projects


class ODKProjectSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les projets ODK (liste)"""

    permission_level = serializers.SerializerMethodField()
    forms_count = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = [
            "id",
            "odk_id",
            "name",
            "description",
            "archived",
            "last_sync",
            "created_at",
            "permission_level",
            "forms_count",
        ]
        read_only_fields = ["id", "odk_id", "last_sync", "created_at"]

    def get_permission_level(self, obj):
        user = self.context["request"].user
        permission = obj.get_user_permission(user)
        return permission.permission_level if permission else None

    def get_forms_count(self, obj):
        return obj.forms.count()


class PublicLinkCreateSerializer(serializers.Serializer):
    """Validate payload to create a public access link for a form"""

    display_name = serializers.CharField(allow_blank=False, max_length=255)
    once = serializers.BooleanField(required=False, default=False)

    def validate_display_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("display_name cannot be empty")
        return cleaned
