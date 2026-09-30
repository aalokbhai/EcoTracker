import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def legacy_in_progress_to_approved(apps, schema_editor):
    """Old 'in progress' complaints had no collector; put them back in the collectors' pool."""
    Complaint = apps.get_model('complaints', 'Complaint')
    Complaint.objects.filter(status='in_progress', collector__isnull=True).update(status='approved')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('complaints', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('in_progress', 'In Progress'), ('cleaned', 'Awaiting Verification'), ('resolved', 'Resolved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AddField(model_name='complaint', name='city', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='complaint', name='state', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='complaint', name='pincode', field=models.CharField(blank=True, max_length=6)),
        migrations.AddField(model_name='complaint', name='reviewed_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='complaint', name='reviewed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='rejection_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='complaint', name='collector', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_complaints', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='complaint', name='assigned_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='started_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='after_image', field=models.ImageField(blank=True, null=True, upload_to='cleaned/')),
        migrations.AddField(model_name='complaint', name='after_ai_score', field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='collector_note', field=models.TextField(blank=True)),
        migrations.AddField(model_name='complaint', name='cleaned_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='verified_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='complaint', name='verified_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='complaint', name='redo_reason', field=models.TextField(blank=True)),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(max_length=20)),
                ('object_id', models.PositiveIntegerField()),
                ('event', models.CharField(choices=[('approved', 'Approved by MC office'), ('rejected', 'Rejected by MC office'), ('assigned', 'Assigned to a collector'), ('accepted', 'Collector started the work'), ('cleaned', 'Cleaning photo uploaded'), ('verified', 'Cleaning verified by MC office'), ('redo', 'Sent back for re-cleaning'), ('cancelled', 'Cancelled by citizen')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('in_progress', 'In Progress'), ('cleaned', 'Awaiting Verification'), ('resolved', 'Resolved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at', 'id'],
                'indexes': [models.Index(fields=['kind', 'object_id'], name='activity_kind_obj_idx')],
            },
        ),
        migrations.RunPython(legacy_in_progress_to_approved, migrations.RunPython.noop),
    ]
