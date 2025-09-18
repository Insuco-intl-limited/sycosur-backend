from rest_framework import serializers

from .models import ProjectPermissions, Projects


class ProjectSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = [
            "id",
            "odk_id",
            "pkid",
            "name",
            "description",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id","pkid","odk_id",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by and obj.created_by.username is not None:
            return obj.created_by.username
        return None

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
