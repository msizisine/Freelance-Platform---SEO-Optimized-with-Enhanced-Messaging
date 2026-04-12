# Generated manually to convert Gig model to Job model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('gigs', '0001_initial'),
    ]

    operations = [
        # Step 1: Add new homeowner field (nullable initially)
        migrations.AddField(
            model_name='gig',
            name='homeowner',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posted_jobs',
                to='core.user'
            ),
        ),
        
        # Step 2: Add new job-related fields
        migrations.AddField(
            model_name='gig',
            name='budget_min',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name='gig',
            name='budget_max',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name='gig',
            name='location',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='gig',
            name='urgency',
            field=models.CharField(
                blank=True,
                choices=[
                    ('asap', 'ASAP'),
                    ('within_week', 'Within a week'),
                    ('within_month', 'Within a month'),
                    ('flexible', 'Flexible')
                ],
                default='flexible',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='gig',
            name='status',
            field=models.CharField(
                choices=[
                    ('open', 'Open'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled')
                ],
                default='open',
                max_length=20
            ),
        ),
        
        # Step 3: Remove old package-related fields
        migrations.RemoveField(
            model_name='gig',
            name='basic_title',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='basic_description',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='basic_price',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='basic_delivery_days',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='standard_title',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='standard_description',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='standard_price',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='standard_delivery_days',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='premium_title',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='premium_description',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='premium_price',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='premium_delivery_days',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='clicks',
        ),
        migrations.RemoveField(
            model_name='gig',
            name='orders_in_queue',
        ),
        
        # Step 4: Remove old freelancer field
        migrations.RemoveField(
            model_name='gig',
            name='freelancer',
        ),
        
        # Step 5: Make homeowner field required
        migrations.AlterField(
            model_name='gig',
            name='homeowner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posted_jobs',
                to='core.user'
            ),
        ),
        
        # Step 6: Make location field required
        migrations.AlterField(
            model_name='gig',
            name='location',
            field=models.CharField(max_length=200),
        ),
    ]
