"""
Migration for Quote Request Models
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_service_provider_models'),
        ('gigs', '0003_add_service_provider_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuoteRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('service_category', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=255)),
                ('preferred_date', models.DateField(blank=True, null=True)),
                ('preferred_time', models.TimeField(blank=True, null=True)),
                ('is_flexible', models.BooleanField(default=False)),
                ('budget_range', models.CharField(blank=True, max_length=100)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('responded', 'Responded'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('whatsapp_flow_id', models.CharField(blank=True, max_length=100)),
                ('whatsapp_message_id', models.CharField(blank=True, max_length=100)),
                ('whatsapp_response_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('homeowner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quote_requests', to='core.user')),
                ('service_provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_quotes', to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['homeowner', 'status']),
                    models.Index(fields=['service_provider', 'status']),
                    models.Index(fields=['created_at']),
                ],
            },
        ),
        migrations.CreateModel(
            name='QuoteResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_type', models.CharField(choices=[('quote', 'Formal Quote'), ('question', 'Question'), ('declined', 'Declined'), ('accepted', 'Accepted')], max_length=20)),
                ('estimated_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('price_description', models.TextField(blank=True)),
                ('estimated_days', models.PositiveIntegerField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('message', models.TextField()),
                ('attachments', models.JSONField(blank=True, null=True)),
                ('whatsapp_flow_response', models.JSONField(blank=True, null=True)),
                ('whatsapp_message_id', models.CharField(blank=True, max_length=100)),
                ('is_accepted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quote_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='gigs.quoterequest')),
                ('service_provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WhatsAppFlowTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('flow_type', models.CharField(choices=[('quote_request', 'Quote Request'), ('quote_response', 'Quote Response'), ('service_confirmation', 'Service Confirmation'), ('feedback', 'Feedback Collection')], max_length=30)),
                ('flow_json', models.JSONField()),
                ('flow_id', models.CharField(max_length=100, unique=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['flow_type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='WhatsAppInteraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=20)),
                ('interaction_type', models.CharField(choices=[('flow_started', 'Flow Started'), ('flow_completed', 'Flow Completed'), ('flow_abandoned', 'Flow Abandoned'), ('message_sent', 'Message Sent'), ('message_received', 'Message Received'), ('button_clicked', 'Button Clicked')], max_length=20)),
                ('whatsapp_message_id', models.CharField(blank=True, max_length=100)),
                ('whatsapp_flow_id', models.CharField(blank=True, max_length=100)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('response_data', models.JSONField(blank=True, null=True)),
                ('processing_status', models.CharField(default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('quote_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gigs.quoterequest')),
                ('quote_response', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gigs.quotesresponse')),
                ('flow_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gigs.whatsappflowtemplate')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['phone_number', 'interaction_type']),
                    models.Index(fields=['created_at']),
                ],
            },
        ),
    ]
