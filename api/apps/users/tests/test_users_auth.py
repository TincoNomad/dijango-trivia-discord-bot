"""
Test suite for user authentication functionality.

This module contains test cases for:
- User login
- User logout
- Authentication error handling
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from .test_data import TEST_USER_DATA

User = get_user_model()

@pytest.mark.django_db
class TestUserAuthentication:
    """Test cases for user authentication flows"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test"""
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.valid_credentials = TEST_USER_DATA['valid_user'].copy()

    @pytest.fixture
    def admin_user(self):
        """Create an admin user with full privileges"""
        user = User.objects.create_user(
            username=self.valid_credentials['username'],
            email=self.valid_credentials['email'],
            password=self.valid_credentials['password'],
            role='admin'
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_authenticated = True
        user.save()
        return user

    def test_successful_login(self, api_client, admin_user):
        """
        Test successful login with valid credentials.
        Should return 200 and auth tokens.
        """
        response = api_client.post(
            self.login_url,
            self.valid_credentials,
            format='json'
        )
        
        # Verify response contains required tokens
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        
        # Verify token works for authenticated endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        me_response = api_client.get('/api/users/')
        assert me_response.status_code == 200

    def test_successful_logout(self, api_client, admin_user):
        """
        Test successful logout flow.
        Should return 205 status code.
        """
        # Login first using the working pattern
        login_response = api_client.post(
            self.login_url,
            self.valid_credentials,
            format='json'
        )
        
        assert login_response.status_code == 200
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login_response.data["access"]}')
        
        # Perform logout
        response = api_client.post(self.logout_url)
        assert response.status_code == 205

    def test_login_with_empty_credentials(self, api_client):
        """
        Test login attempt with empty credentials.
        Should return 400 with field validation errors.
        """
        response = api_client.post(self.login_url, {}, format='json')
        assert response.status_code == 400
        # Verify both fields are required
        assert 'username' in response.data
        assert 'password' in response.data
        assert 'This field is required.' in str(response.data['username'])
        assert 'This field is required.' in str(response.data['password'])

    @pytest.mark.parametrize("invalid_credentials,expected_status,expected_error", [
        (
            {'username': '', 'password': 'test123'}, 
            400, 
            'This field may not be blank'
        ),
        (
            {'username': 'test', 'password': ''}, 
            400, 
            'This field may not be blank'
        ),
        (
            {'username': 'test', 'password': 'wrong'}, 
            401, 
            'No active account found'
        )
    ])
    def test_login_failures(self, api_client, invalid_credentials, expected_status, expected_error):
        """Test diferentes escenarios de fallo de login
        
        Args:
            invalid_credentials: Credenciales inválidas a probar
            expected_status: Código de estado HTTP esperado
            expected_error: Mensaje de error esperado
            
        Verifica:
            - 400: Para errores de validación (campos vacíos)
            - 401: Para credenciales incorrectas
        """
        response = api_client.post(self.login_url, invalid_credentials, format='json')
        assert response.status_code == expected_status, (
            f"Se esperaba {expected_status} para las credenciales: {invalid_credentials}"
        )
        
        if expected_status == 400:
            # Verificar mensaje de error de validación
            error_messages = [str(error) for error in response.data.values()]
            assert any(
                expected_error in error_msg
                for error_msg in error_messages
            ), f"Debería contener el mensaje '{expected_error}'. Mensajes recibidos: {error_messages}"
        else:
            # Verificar mensaje de credenciales inválidas
            assert expected_error in str(response.data['detail']), (
                f"Debería contener el mensaje '{expected_error}'"
            )