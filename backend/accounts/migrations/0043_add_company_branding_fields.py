# Generated migration for company branding fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0042_add_assigned_to_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='company_logo',
            field=models.ImageField(blank=True, help_text='Company logo for branded PDF reports', null=True, upload_to='company_logos/'),
        ),
        migrations.AddField(
            model_name='user',
            name='brand_style',
            field=models.JSONField(blank=True, default=dict, help_text='AI-generated brand style guide: colors, fonts, layout preferences. Generated from logo analysis.'),
        ),
    ]
