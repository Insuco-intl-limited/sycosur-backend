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
