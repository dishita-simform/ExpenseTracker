from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from allauth.socialaccount.providers.google.provider import GoogleProvider

class Command(BaseCommand):
    help = 'Sets up Google OAuth2 configuration'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', required=True, help='Google OAuth2 client ID')
        parser.add_argument('--secret', required=True, help='Google OAuth2 client secret')
        parser.add_argument('--site-domain', default='127.0.0.1:8000', help='Site domain')
        parser.add_argument('--site-name', default='localhost', help='Site name')

    def handle(self, *args, **options):
        # Get or create the site
        try:
            site = Site.objects.get(domain=options['site_domain'])
        except Site.DoesNotExist:
            # If no site exists with this domain, get the first site or create a new one
            site = Site.objects.first()
            if not site:
                site = Site.objects.create(
                    domain=options['site_domain'],
                    name=options['site_name']
                )
            else:
                # Update the existing site
                site.domain = options['site_domain']
                site.name = options['site_name']
                site.save()

        # Create or update the social app
        social_app, created = SocialApp.objects.get_or_create(
            provider=GoogleProvider.id,
            defaults={
                'name': 'Google',
                'client_id': options['client_id'],
                'secret': options['secret'],
            }
        )

        if not created:
            social_app.client_id = options['client_id']
            social_app.secret = options['secret']
            social_app.save()

        # Make sure the site is associated with the social app
        social_app.sites.add(site)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully {"created" if created else "updated"} Google OAuth2 configuration'
        )) 