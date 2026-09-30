import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('citizen', 'Citizen'), ('collector', 'Garbage Collector'), ('officer', 'MC Officer')], default='citizen', max_length=20)),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('city', models.CharField(blank=True, max_length=80)),
                ('state', models.CharField(blank=True, max_length=80)),
                ('pincode', models.CharField(blank=True, max_length=6)),
                ('is_approved', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
