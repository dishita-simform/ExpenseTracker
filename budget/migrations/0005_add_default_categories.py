# Generated manually

from django.db import migrations

def create_default_categories(apps, schema_editor):
    Category = apps.get_model('budget', 'Category')
    User = apps.get_model('auth', 'User')

    # Default category data with colors and icons
    default_categories = [
        {'name': 'Rent', 'color': '#4B0082', 'icon': 'home', 'description': 'Housing and rental expenses'},
        {'name': 'Food', 'color': '#32CD32', 'icon': 'utensils', 'description': 'Groceries and dining out'},
        {'name': 'Travel', 'color': '#1E90FF', 'icon': 'plane', 'description': 'Travel and vacation expenses'},
        {'name': 'Bills', 'color': '#DC143C', 'icon': 'file-invoice-dollar', 'description': 'Regular monthly bills'},
        {'name': 'Entertainment', 'color': '#FF69B4', 'icon': 'film', 'description': 'Movies, games, and entertainment'},
        {'name': 'Shopping', 'color': '#FF4500', 'icon': 'shopping-cart', 'description': 'General shopping expenses'},
        {'name': 'Healthcare', 'color': '#FF6347', 'icon': 'hospital', 'description': 'Medical and healthcare expenses'},
        {'name': 'Education', 'color': '#6A5ACD', 'icon': 'graduation-cap', 'description': 'Education and learning expenses'},
        {'name': 'Transportation', 'color': '#FFD700', 'icon': 'car', 'description': 'Vehicle and transportation costs'},
        {'name': 'Utilities', 'color': '#00CED1', 'icon': 'bolt', 'description': 'Utility bills and services'},
        {'name': 'Insurance', 'color': '#8A2BE2', 'icon': 'shield-alt', 'description': 'Insurance premiums'},
        {'name': 'Savings', 'color': '#20B2AA', 'icon': 'piggy-bank', 'description': 'Savings and emergency fund'},
        {'name': 'Investment', 'color': '#FF8C00', 'icon': 'chart-line', 'description': 'Investment and trading'},
        {'name': 'Gifts', 'color': '#DA70D6', 'icon': 'gift', 'description': 'Gifts and donations'},
        {'name': 'Fitness', 'color': '#40E0D0', 'icon': 'dumbbell', 'description': 'Gym and fitness expenses'},
        {'name': 'Pet', 'color': '#FF69B4', 'icon': 'paw', 'description': 'Pet care and supplies'},
        {'name': 'Home', 'color': '#4B0082', 'icon': 'home', 'description': 'Home maintenance and decor'},
        {'name': 'Personal Care', 'color': '#32CD32', 'icon': 'spa', 'description': 'Personal care and grooming'},
        {'name': 'Other', 'color': '#6c757d', 'icon': 'ellipsis-h', 'description': 'Miscellaneous expenses'}
    ]

    # Get or create a default user if no users exist
    default_user = User.objects.first()
    if not default_user:
        default_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    # Create categories for the default user
    for cat_data in default_categories:
        Category.objects.get_or_create(
            user=default_user,
            name=cat_data['name'],
            defaults={
                'color': cat_data['color'],
                'icon': cat_data['icon'],
                'description': cat_data['description'],
                'is_active': True,
                'budget': 0
            }
        )

def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('budget', 'Category')
    Category.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0004_add_category_description'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ] 