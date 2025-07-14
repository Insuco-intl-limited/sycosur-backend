from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError

from core_apps.profiles.models import Profile
from ..services import ODKCentralService

User = get_user_model()


class ODKConnectionTests(TestCase):
    def setUp(self):
        # Créer un utilisateur administrateur
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.profile.odk_role = Profile.ODKRole.ADMINISTRATOR
        self.admin_user.profile.save()

        # Créer un utilisateur normal
        self.normal_user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Normal',
            last_name='User'
        )
        self.normal_user.profile.odk_role = Profile.ODKRole.DATA_COLLECTOR
        self.normal_user.profile.save()

    @override_settings(ODK_CENTRAL_URL='http://test.example.com/v1')
    @patch('core_apps.odk.services.ODKCentralService._make_request')
    def test_odk_connection_success(self, mock_make_request):
        """Test d'une connexion réussie à ODK Central"""
        # Configurer le mock pour simuler une réponse réussie
        mock_make_request.return_value = [
            {'id': 1, 'name': 'Test Project 1'},
            {'id': 2, 'name': 'Test Project 2'}
        ]

        # Connecter l'utilisateur admin
        self.client.login(email='admin@example.com', password='password123')

        # Appeler l'API status
        response = self.client.get(reverse('odk:system-status'))

        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['odk_status']['status'], 'online')

        # Vérifier que le mock a été appelé correctement
        mock_make_request.assert_called_once_with('GET', 'projects')

    @override_settings(ODK_CENTRAL_URL='http://test.example.com/v1')
    @patch('core_apps.odk.services.ODKCentralService._make_request')
    def test_odk_connection_failure(self, mock_make_request):
        """Test d'une connexion échouée à ODK Central"""
        # Configurer le mock pour simuler une erreur de connexion
        mock_make_request.side_effect = ConnectionError("Connection refused")

        # Connecter l'utilisateur admin
        self.client.login(email='admin@example.com', password='password123')

        # Appeler l'API status
        response = self.client.get(reverse('odk:system-status'))

        # Vérifier la réponse
        self.assertEqual(response.status_code, 503)  # Service Unavailable
        data = response.json()
        self.assertEqual(data['odk_status']['status'], 'offline')
        self.assertIn('error', data['odk_status'])

    @override_settings(ODK_CENTRAL_URL='invalid-url')
    def test_invalid_odk_url(self):
        """Test avec une URL ODK invalide"""
        # Connecter l'utilisateur admin
        self.client.login(email='admin@example.com', password='password123')

        # Appeler l'API status
        response = self.client.get(reverse('odk:system-status'))

        # Vérifier la réponse
        self.assertEqual(response.status_code, 503)  # Service Unavailable
        data = response.json()
        self.assertEqual(data['odk_status']['status'], 'offline')
        self.assertIn('error', data['odk_status'])

    def test_unauthorized_access(self):
        """Test d'accès non autorisé à l'API ODK"""
        # Sans connexion
        response = self.client.get(reverse('odk:system-status'))
        self.assertEqual(response.status_code, 401)  # Unauthorized

        # Connecter un utilisateur normal
        self.client.login(email='user@example.com', password='password123')

        # L'utilisateur normal devrait avoir accès car il a un rôle ODK
        response = self.client.get(reverse('odk:system-status'))
        self.assertEqual(response.status_code, 200)
