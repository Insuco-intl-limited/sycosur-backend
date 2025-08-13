from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import ODKProjectPermissions, ODKProjects, User

# User = get_user_model()

class ODKCreateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ODKProjects
        fields = ["name", "description"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ODKProjectSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les projets ODK (liste)"""

    permission_level = serializers.SerializerMethodField()
    forms_count = serializers.SerializerMethodField()

    class Meta:
        model = ODKProjects
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


class ODKProjectPermissionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les permissions de projet ODK"""

    user_email = serializers.ReadOnlyField(source="user.email")
    user_full_name = serializers.SerializerMethodField()
    project_name = serializers.ReadOnlyField(source="project.name")
    granted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ODKProjectPermissions
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


# class ODKSubmissionSerializer(serializers.Serializer):
#     """Sérialiseur pour les soumissions ODK (structure dynamique)"""
#     id = serializers.CharField(read_only=True)
#     instanceId = serializers.CharField(read_only=True)
#     submitterId = serializers.CharField(read_only=True)
#     deviceId = serializers.CharField(read_only=True, required=False, allow_null=True)
#     createdAt = serializers.DateTimeField(read_only=True)
#     updatedAt = serializers.DateTimeField(read_only=True)
#     submitterName = serializers.CharField(read_only=True, required=False, allow_null=True)
#     attachmentsPresent = serializers.IntegerField(read_only=True, required=False)
#     attachmentsExpected = serializers.IntegerField(read_only=True, required=False)
#     # Le contenu effectif de la soumission est dynamique
#     content = serializers.JSONField(read_only=True)
