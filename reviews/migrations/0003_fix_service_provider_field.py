# Generated to add service_provider_id_id field to match database

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_fix_service_provider_field'),
    ]

    operations = [
        # Add service_provider_id_id field to match database column
        migrations.AddField(
            model_name='review',
            name='service_provider_id_id',
            field=models.ForeignKey(
                to='auth.User',
                on_delete=models.CASCADE,
                related_name='reviews_received_alt',
                null=True,
                blank=True
            ),
        ),
    ]
