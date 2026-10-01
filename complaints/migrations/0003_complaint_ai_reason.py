from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='ai_reason',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
