from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from budget.models import Category
from budget.constants import DEFAULT_CATEGORIES, DEFAULT_CATEGORY_ICONS

class Command(BaseCommand):
    help = 'Create default categories for all existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            for category_name, color in DEFAULT_CATEGORIES.items():
                if not Category.objects.filter(user=user, name=category_name).exists():
                    Category.objects.create(
                        user=user,
                        name=category_name,
                        color=color,
                        icon=DEFAULT_CATEGORY_ICONS.get(category_name, 'receipt')
                    )
        self.stdout.write(self.style.SUCCESS('Default categories created for all users.'))