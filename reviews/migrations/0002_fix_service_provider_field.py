# Generated to add service_provider_id column if missing

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        # Add service_provider_id column if it doesn't exist
        migrations.AddField(
            model_name='review',
            name='service_provider_id',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name='reviews_received',
                null=True,
                blank=True
            ),
        ),
    ]
