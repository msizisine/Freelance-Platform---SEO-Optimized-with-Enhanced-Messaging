# Generated to fix service_provider field naming issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0003_fix_service_provider_field'),
    ]

    operations = [
        # Rename service_provider_id_id to service_provider_id
        migrations.RenameField(
            model_name='review',
            old_name='service_provider_id_id',
            new_name='service_provider_id',
        ),
    ]
