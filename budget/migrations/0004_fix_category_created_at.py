# Generated manually

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_alter_category_options_category_created_at_and_more'),
    ]

    operations = [
        # First, remove the created_at field
        migrations.RemoveField(
            model_name='category',
            name='created_at',
        ),
        # Then add it back with a proper default
        migrations.AddField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        # Finally, change it to auto_now_add
        migrations.AlterField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ] 