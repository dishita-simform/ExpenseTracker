from django.db import migrations
from django.utils import timezone

def set_default_created_at(apps, schema_editor):
    Category = apps.get_model('budget', 'Category')
    for category in Category.objects.filter(created_at__isnull=True):
        category.created_at = timezone.now()
        category.save()

class Migration(migrations.Migration):
    dependencies = [
        ('budget', 'previous_migration'),  # Replace with your actual previous migration
    ]

    operations = [
        migrations.RunPython(set_default_created_at),
    ] 