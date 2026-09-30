from django.db import migrations


def create_profiles(apps, schema_editor):
    """Give every already-existing account a profile (staff -> officer)."""
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('accounts', 'Profile')
    for user in User.objects.all():
        Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'officer' if user.is_staff else 'citizen'},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_profiles, migrations.RunPython.noop),
    ]
