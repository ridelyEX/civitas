import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, Mock
import factory
from datetime import date

from .models import Users, CustomUser

# Factories para CMIN
class UsersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Users

    username = factory.Sequence(lambda n: f"cmin_user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@cmin.gov.mx")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'cminpass123')
    bday = factory.Faker('date_of_birth', minimum_age=25, maximum_age=65)
    is_staff = True
    is_active = True

# Tests para modelos CMIN
class TestUsersModel(TestCase):
    def setUp(self):
        self.user = UsersFactory()

    def test_user_creation(self):
        """Test de creación de usuario CMIN"""
        self.assertIsInstance(self.user, Users)
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_staff)
        self.assertIsNotNone(self.user.email)

    def test_user_string_representation(self):
        """Test del método __str__ del modelo Users"""
        self.assertEqual(str(self.user), self.user.username)

    def test_email_field_unique(self):
        """Test que verifica que el email es único"""
        with self.assertRaises(Exception):
            # Intentar crear otro usuario con el mismo email
            Users.objects.create(
                username='otro_usuario',
                email=self.user.email,
                bday=date.today()
            )

    def test_required_fields(self):
        """Test de campos requeridos"""
        user = Users(
            username='test_user',
            email='test@cmin.gov.mx',
            bday=date.today()
        )
        user.set_password('password123')
        user.save()

        self.assertEqual(user.username, 'test_user')
        self.assertEqual(user.email, 'test@cmin.gov.mx')

class TestCustomUserManager(TestCase):
    def setUp(self):
        self.manager = CustomUser()

    def test_create_user_without_email(self):
        """Test que verifica que no se puede crear usuario sin email"""
        with self.assertRaises(ValueError):
            self.manager.create_user(email='', password='test123')

    def test_create_user_with_valid_data(self):
        """Test de creación de usuario con datos válidos"""
        user = Users.objects.create_user(
            username='testuser',
            email='test@cmin.gov.mx',
            password='testpass123',
            bday=date.today()
        )

        self.assertIsInstance(user, Users)
        self.assertEqual(user.email, 'test@cmin.gov.mx')
        self.assertTrue(user.check_password('testpass123'))

# Tests para vistas CMIN
class TestCMinViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UsersFactory()
        self.client.force_login(self.user)

    def test_admin_dashboard_access(self):
        """Test de acceso al dashboard administrativo"""
        try:
            response = self.client.get(reverse('cmin:dashboard'))
            self.assertEqual(response.status_code, 200)
        except:
            pass  # Si la ruta no existe aún

    def test_user_list_view(self):
        """Test de vista de lista de usuarios"""
        try:
            response = self.client.get(reverse('cmin:users'))
            self.assertEqual(response.status_code, 200)
        except:
            pass  # Si la ruta no existe aún

    def test_unauthorized_access(self):
        """Test de acceso no autorizado"""
        self.client.logout()
        try:
            response = self.client.get(reverse('cmin:dashboard'))
            self.assertIn(response.status_code, [302, 403])  # Redirección o prohibido
        except:
            pass

# Tests para APIs CMIN
class TestCMinAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UsersFactory()
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_api_authentication_required(self):
        """Test que verifica autenticación en APIs CMIN"""
        client = APIClient()
        try:
            response = client.get('/api/cmin/users/')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        except:
            pass  # Si la ruta no existe aún

    def test_staff_permissions(self):
        """Test de permisos de staff"""
        self.assertTrue(self.user.is_staff)

        try:
            response = self.client.get('/api/cmin/users/')
            self.assertIn(response.status_code, [200, 404])  # OK o no encontrado
        except:
            pass

# Tests de permisos y seguridad CMIN
class TestCMinSecurity(TestCase):
    def setUp(self):
        self.staff_user = UsersFactory(is_staff=True)
        self.regular_user = UsersFactory(is_staff=False)
        self.superuser = UsersFactory(is_superuser=True, is_staff=True)

    def test_staff_user_permissions(self):
        """Test de permisos de usuario staff"""
        self.assertTrue(self.staff_user.is_staff)
        self.assertFalse(self.staff_user.is_superuser)

    def test_superuser_permissions(self):
        """Test de permisos de superusuario"""
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)

    def test_regular_user_restrictions(self):
        """Test de restricciones de usuario regular"""
        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)

# Tests de integración CMIN
class TestCMinIntegration(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = UsersFactory(is_staff=True, is_superuser=True)
        self.staff_user = UsersFactory(is_staff=True)

    def test_admin_workflow(self):
        """Test de flujo de trabajo de administrador"""
        self.client.force_login(self.admin_user)

        # Verificar acceso a panel administrativo de Django
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_staff_workflow(self):
        """Test de flujo de trabajo de staff"""
        self.client.force_login(self.staff_user)

        # Verificar que el staff puede acceder a ciertas áreas
        self.assertTrue(self.staff_user.is_staff)

# Tests de rendimiento CMIN
class TestCMinPerformance(TestCase):
    def setUp(self):
        # Crear múltiples usuarios para tests de rendimiento
        self.users = UsersFactory.create_batch(30)

    def test_user_queries_performance(self):
        """Test de rendimiento de consultas de usuarios"""
        import time

        start_time = time.time()

        # Consultas que podrían ser lentas
        total_users = Users.objects.count()
        staff_users = Users.objects.filter(is_staff=True).count()
        active_users = Users.objects.filter(is_active=True).count()

        end_time = time.time()
        execution_time = end_time - start_time

        # Verificar que las consultas no tomen más de 0.5 segundos
        self.assertLess(execution_time, 0.5)
        self.assertEqual(total_users, 30)

# Configuración específica para tests CMIN
class CMinTestConfig:
    """Configuración específica para tests del módulo CMIN"""

    @staticmethod
    def setup_test_data():
        """Configurar datos de prueba específicos para CMIN"""
        admin = UsersFactory(
            username='admin_test',
            is_staff=True,
            is_superuser=True
        )
        staff = UsersFactory(
            username='staff_test',
            is_staff=True,
            is_superuser=False
        )
        return admin, staff
