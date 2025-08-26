from rest_framework import serializers

from .models import ProjectPermissions, Projects, User


class CreateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = ["name", "description"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ProjectPermissionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les permissions de projet ODK"""

    user_email = serializers.ReadOnlyField(source="user.email")
    user_full_name = serializers.SerializerMethodField()
    project_name = serializers.ReadOnlyField(source="project.name")
    granted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPermissions
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "project",
            "project_name",
            "permission_level",
            "granted_by",
            "granted_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_full_name",
            "project_name",
            "granted_by_name",
            "created_at",
        ]

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()

    def get_granted_by_name(self, obj):
        if obj.granted_by:
            return obj.granted_by.get_full_name()
        return None

    def validate(self, attrs):
        # S'assurer que l'utilisateur actuel est défini comme celui qui accorde la permission
        attrs["granted_by"] = self.context["request"].user
        return attrs
