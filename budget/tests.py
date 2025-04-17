from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.contrib.messages import get_messages

class PasswordResetTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.password_reset_url = reverse('password_reset')
        self.password_reset_done_url = reverse('password_reset_done')
        self.password_reset_confirm_url = reverse('password_reset_confirm', kwargs={'uidb64': 'uid', 'token': 'token'})
        self.password_reset_complete_url = reverse('password_reset_complete')

    def test_password_reset_view_status_code(self):
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)

    def test_password_reset_template_used(self):
        response = self.client.get(self.password_reset_url)
        self.assertTemplateUsed(response, 'registration/password_reset.html')  # Correct template name

    def test_password_reset_email_sent(self):
        response = self.client.post(self.password_reset_url, {'email': self.user.email})
        self.assertEqual(response.status_code, 302)  # Redirect to password_reset_done
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)  # Ensure one message is present
        self.assertIn('Password reset link has been sent to testuser@example.com', str(messages[0]))  # Correct message content
        self.assertEqual(len(mail.outbox), 1)  # Email sent
        self.assertIn('testuser@example.com', mail.outbox[0].to)

    def test_password_reset_done_view_status_code(self):
        response = self.client.get(self.password_reset_done_url)
        self.assertEqual(response.status_code, 200)

    def test_password_reset_done_template_used(self):
        response = self.client.get(self.password_reset_done_url)
        self.assertTemplateUsed(response, 'registration/password_reset_done.html')

    def test_password_reset_confirm_view_status_code(self):
        response = self.client.get(self.password_reset_confirm_url)
        self.assertEqual(response.status_code, 200)

    def test_password_reset_confirm_template_used(self):
        response = self.client.get(self.password_reset_confirm_url)
        self.assertTemplateUsed(response, 'registration/password_reset_confirm.html')

    def test_password_reset_complete_view_status_code(self):
        response = self.client.get(self.password_reset_complete_url)
        self.assertEqual(response.status_code, 200)

    def test_password_reset_complete_template_used(self):
        response = self.client.get(self.password_reset_complete_url)
        self.assertTemplateUsed(response, 'registration/password_reset_complete.html')