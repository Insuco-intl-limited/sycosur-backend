from typing import List

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import Http404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer

from .models import Profile
from .serializers import (
    AvatarUploadSerializer,
    ProfileSerializer,
    UpdateProfileSerializer,
)
from .tasks import upload_avatar_to_google_drive
from ..common.drive_storage import GoogleDriveStorage

# from rest_framework.response import Response
# from rest_framework.views import APIView


# from .tasks import upload_avatar_to_cloudinary

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100


class ProfileListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJSONRenderer]
    pagination_class = StandardResultsSetPagination
    object_label = "profiles"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name"]
    filterset_fields = ["odk_role", "gender", "country_of_origin"]

    def get_queryset(self) -> List[Profile]:
        return (
            Profile.objects.exclude(user__is_staff=True)
            .exclude(user__is_superuser=True)
            .filter(odk_role=Profile.ODKRole.DATA_COLLECTOR)
        )


class ProfileDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "profile"

    def get_queryset(self) -> QuerySet:
        return Profile.objects.select_related("user").all()

    def get_object(self) -> Profile:
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            raise Http404("Profile not found")


class ProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UpdateProfileSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "profile"

    def get_queryset(self):
        return Profile.objects.none()

    def get_object(self) -> Profile:
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer: UpdateProfileSerializer) -> Profile:
        user_data = serializer.validated_data.pop("user", {})
        profile = serializer.save()
        User.objects.filter(id=self.request.user.id).update(**user_data)
        return profile


class AvatarUploadView(APIView):
    def patch(self, request, *args, **kwargs):
        return self.upload_avatar(request, *args, **kwargs)

    def upload_avatar(self, request, *args, **kwargs):
        profile = request.user.profile
        serializer = AvatarUploadSerializer(profile, data=request.data)

        if serializer.is_valid():
            image = serializer.validated_data["avatar"]

            profile.avatar = image
            profile.save()

            return Response(
                {"message": "Avatar uploaded successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAvatarView(APIView):

    @action(detail=True, methods=['delete'])
    def delete_avatar(self, request):
        try:
            profile = request.user.profile
            if not profile:
                return Response(
                    {"message": "Profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not profile.avatar:
                return Response(
                    {"message": "No avatar to delete"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            storage = GoogleDriveStorage()
            image_name = storage.get_image_name(profile.avatar)

            try:
                storage.delete(image_name)
                profile.avatar = None
                profile.save()
                return Response(
                    {"message": "Avatar deleted successfully"},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"message": f"Failed to delete avatar: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
