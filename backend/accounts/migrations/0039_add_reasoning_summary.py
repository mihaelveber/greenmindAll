# Generated migration for adding reasoning_summary field to AITaskStatus

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0038_update_rag_tier_thresholds'),
    ]

    operations = [
        migrations.AddField(
            model_name='aitaskstatus',
            name='reasoning_summary',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='AI reasoning summary from OpenAI o1 models (gpt-5, gpt-5-mini, gpt-5-nano). Shows thinking process before generating answer.'
            ),
        ),
    ]
