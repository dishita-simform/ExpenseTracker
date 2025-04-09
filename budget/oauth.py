from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
import ssl
import requests

class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def get_access_token(self, request, app):
        """
        Override to handle SSL certificate verification issues
        """
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Use the custom SSL context for requests
        session = requests.Session()
        session.verify = False
        
        # Disable SSL verification warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Call the parent method with our custom session
        return super().get_access_token(request, app)

class CustomOAuth2Client(OAuth2Client):
    def get_access_token(self, code, pkce_code_verifier=None):
        """
        Override to handle SSL certificate verification issues
        """
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Use the custom SSL context for requests
        session = requests.Session()
        session.verify = False
        
        # Disable SSL verification warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Call the parent method with our custom session
        return super().get_access_token(code, pkce_code_verifier) 