from django.db import migrations, models


DEFAULT_PROFILE_PHOTO = "defaults/user_avatar.svg"
OLD_DEFAULT_PROFILE_PHOTO = "defaults/user_avatar.png"


def set_default_avatar(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    Profile.objects.filter(profile_photo__isnull=True).update(profile_photo=DEFAULT_PROFILE_PHOTO)
    Profile.objects.filter(profile_photo="").update(profile_photo=DEFAULT_PROFILE_PHOTO)
    Profile.objects.filter(profile_photo=OLD_DEFAULT_PROFILE_PHOTO).update(profile_photo=DEFAULT_PROFILE_PHOTO)


def revert_default_avatar(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    Profile.objects.filter(profile_photo=DEFAULT_PROFILE_PHOTO).update(profile_photo=OLD_DEFAULT_PROFILE_PHOTO)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_profile_phone_profile_total_reviews_devicetoken_and_more"),
    ]

    operations = [
        migrations.RunPython(set_default_avatar, revert_default_avatar),
        migrations.AlterField(
            model_name="profile",
            name="profile_photo",
            field=models.ImageField(
                default=DEFAULT_PROFILE_PHOTO,
                upload_to="profile_photos/",
            ),
        ),
    ]
