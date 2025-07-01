# from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
from django.db import models

# from django.db.models import Avg
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

from core_apps.common.models import TimeStampedModel

User = get_user_model()


def get_user_username(instance: "Profile") -> str:
    return instance.user.username


class Profile(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = (
            "male",
            _("Male"),
        )
        FEMALE = (
            "female",
            _("Female"),
        )
        OTHER = (
            "other",
            _("Other"),
        )

    class ODKRole(models.TextChoices):
        DATA_COLLECTOR = (
            "data_collector",
            _("Data Collector"),
        )
        SUPERVISOR = (
            "supervisor",
            _("Supervisor"),
        )
        MANAGER = (
            "manager",
            _("Manager"),
        )
        ADMINISTRATOR = (
            "administrator",
            _("Administrator"),
        )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # avatar = CloudinaryField(verbose_name=_("Avatar"), blank=True, null=True)
    gender = models.CharField(
        verbose_name=_("Gender"),
        max_length=10,
        choices=Gender.choices,
        default=Gender.OTHER,
    )
    bio = models.TextField(verbose_name=_("Bio"), blank=True, null=True)
    odk_role = models.CharField(
        verbose_name=_("ODK Role"),
        max_length=20,
        choices=ODKRole.choices,
        default=ODKRole.DATA_COLLECTOR,
    )
    phone_number = PhoneNumberField(
        verbose_name=_("Phone Number"), max_length=30, default="+250784123456"
    )
    country_of_origin = CountryField(verbose_name=_("Country"), default="KE")
    city_of_origin = models.CharField(
        verbose_name=_("City"), max_length=180, default="Nairobi"
    )

    slug = AutoSlugField(populate_from=get_user_username, unique=True)

    def __str__(self) -> str:
        return f"{self.user.first_name}'s Profile"
