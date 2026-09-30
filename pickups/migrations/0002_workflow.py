import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def map_old_statuses(apps, schema_editor):
    """Old pickup statuses -> new workflow statuses."""
    Pickup = apps.get_model('pickups', 'PickupRequest')
    Pickup.objects.filter(status='scheduled').update(status='approved')
    Pickup.objects.filter(status='completed').update(status='resolved')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pickups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(model_name='pickuprequest', name='area', field=models.CharField(blank=True, max_length=100)),
        migrations.AlterField(
            model_name='pickuprequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('in_progress', 'In Progress'), ('cleaned', 'Awaiting Verification'), ('resolved', 'Resolved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AddField(model_name='pickuprequest', name='city', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='pickuprequest', name='state', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='pickuprequest', name='pincode', field=models.CharField(blank=True, max_length=6)),
        migrations.AddField(model_name='pickuprequest', name='reviewed_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='pickuprequest', name='reviewed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='rejection_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='pickuprequest', name='collector', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_pickuprequests', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='pickuprequest', name='assigned_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='started_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='after_image', field=models.ImageField(blank=True, null=True, upload_to='cleaned/')),
        migrations.AddField(model_name='pickuprequest', name='after_ai_score', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='collector_note', field=models.TextField(blank=True)),
        migrations.AddField(model_name='pickuprequest', name='cleaned_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='verified_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='pickuprequest', name='verified_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='pickuprequest', name='redo_reason', field=models.TextField(blank=True)),
        migrations.RunPython(map_old_statuses, migrations.RunPython.noop),
    ]
