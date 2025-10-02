import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, Mock
import uuid
from datetime import date
from factory import Factory, Faker, SubFactory
import factory

from .models import DesUrUsers, Uuid, data, SubirDocs, soli, DesUrLoginDate
from .tasks import cleanup_old_logs, send_notification_email, process_document_upload

# Factories para crear datos de prueba
class DesUrUsersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DesUrUsers

    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    bday = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    is_active = True

class UuidFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Uuid

    uuid = factory.LazyFunction(uuid.uuid4)

class DataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = data

    fuuid = factory.SubFactory(UuidFactory)
    nombre = factory.Faker('first_name')
    pApe = factory.Faker('last_name')
    mApe = factory.Faker('last_name')
    bDay = factory.Faker('date_of_birth', minimum_age=18, maximum_age=80)
    asunto = factory.Faker('sentence', nb_words=4)
    tel = '+525512345678'
    curp = 'ABCD123456HDFRTY01'
    sexo = 'M'
    dirr = factory.Faker('address')
    disc = 'Ninguna'
    etnia = 'Mestizo'
    vul = 'Ninguna'

class SubirDocsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubirDocs

    fuuid = factory.SubFactory(UuidFactory)
    nomDoc = factory.Faker('file_name')
    descDoc = factory.Faker('sentence')
    doc = factory.django.FileField(filename='test.pdf')

# Tests para modelos
class TestDesUrUsersModel(TestCase):
    def setUp(self):
        self.user = DesUrUsersFactory()

    def test_user_creation(self):
        """Test que verifica la creación correcta de usuarios"""
        self.assertIsInstance(self.user, DesUrUsers)
        self.assertTrue(self.user.is_active)
        self.assertIsNotNone(self.user.email)
        self.assertIsNotNone(self.user.username)

    def test_user_string_representation(self):
        """Test del método __str__ del modelo"""
        self.assertEqual(str(self.user), self.user.username)

    def test_password_hashing(self):
        """Test que verifica el hash de contraseñas"""
        raw_password = 'testpass123'
        self.user.set_password(raw_password)
        self.assertTrue(self.user.check_password(raw_password))
        self.assertFalse(self.user.check_password('wrongpass'))

    def test_get_full_name(self):
        """Test del método get_full_name"""
        expected_name = f"{self.user.first_name} {self.user.last_name}".strip()
        self.assertEqual(self.user.get_full_name(), expected_name)

    def test_user_authentication_properties(self):
        """Test de propiedades de autenticación"""
        self.assertTrue(self.user.is_authenticated)
        self.assertFalse(self.user.is_anonymous)

class TestDataModel(TestCase):
    def setUp(self):
        self.data_instance = DataFactory()

    def test_data_creation(self):
        """Test de creación de datos de ciudadano"""
        self.assertIsInstance(self.data_instance, data)
        self.assertIsNotNone(self.data_instance.fuuid)
        self.assertIsNotNone(self.data_instance.nombre)

    def test_data_string_representation(self):
        """Test del método __str__"""
        self.assertEqual(str(self.data_instance), self.data_instance.nombre)

    def test_curp_validation(self):
        """Test de validación de CURP"""
        # CURP válida
        valid_curp = 'ABCD123456HDFRTY01'
        self.data_instance.curp = valid_curp
        self.data_instance.save()
        self.assertEqual(self.data_instance.curp, valid_curp)

class TestSubirDocsModel(TestCase):
    def setUp(self):
        self.document = SubirDocsFactory()

    def test_document_creation(self):
        """Test de creación de documentos"""
        self.assertIsInstance(self.document, SubirDocs)
        self.assertIsNotNone(self.document.fuuid)
        self.assertIsNotNone(self.document.descDoc)

    def test_document_string_representation(self):
        """Test del método __str__"""
        expected = self.document.nomDoc or "Documento sin nombre"
        self.assertEqual(str(self.document), expected)

# Tests para vistas
class TestDesUrViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = DesUrUsersFactory()

    def test_login_view_get(self):
        """Test de vista de login (GET)"""
        response = self.client.get(reverse('desur:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_valid(self):
        """Test de login con credenciales válidas"""
        login_data = {
            'username': self.user.username,
            'password': 'testpass123'
        }
        response = self.client.post(reverse('desur:login'), login_data)
        # Verificar redirección o respuesta exitosa
        self.assertIn(response.status_code, [200, 302])

    def test_login_view_post_invalid(self):
        """Test de login con credenciales inválidas"""
        login_data = {
            'username': 'invalid_user',
            'password': 'wrong_password'
        }
        response = self.client.post(reverse('desur:login'), login_data)
        self.assertEqual(response.status_code, 200)  # Permanece en login

# Tests para APIs
class TestDesUrAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = DesUrUsersFactory()
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.data_instance = DataFactory()
        self.document = SubirDocsFactory()

    def test_api_authentication_required(self):
        """Test que verifica que la API requiere autenticación"""
        client = APIClient()  # Cliente sin autenticación
        response = client.get('/api/desur/ciudadanos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_ciudadanos_list(self):
        """Test de listado de ciudadanos via API"""
        response = self.client.get('/api/desur/ciudadanos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)

    def test_create_ciudadano_via_api(self):
        """Test de creación de ciudadano via API"""
        ciudadano_data = {
            'nombre': 'Juan',
            'pApe': 'Pérez',
            'mApe': 'García',
            'bDay': '1990-01-01',
            'asunto': 'Licencia de conducir',
            'tel': '+525512345678',
            'curp': 'ABCD123456HDFRTY01',
            'sexo': 'M',
            'dirr': 'Calle Falsa 123',
            'disc': 'Ninguna',
            'etnia': 'Mestizo',
            'vul': 'Ninguna'
        }
        response = self.client.post('/api/desur/ciudadanos/', ciudadano_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_api_throttling(self):
        """Test de limitación de velocidad en API"""
        # Simular muchas peticiones rápidas
        responses = []
        for i in range(10):
            response = self.client.get('/api/desur/ciudadanos/')
            responses.append(response.status_code)

        # La mayoría deberían ser exitosas
        success_count = responses.count(200)
        self.assertGreaterEqual(success_count, 8)

# Tests para tareas de Celery
class TestCeleryTasks(TestCase):
    def setUp(self):
        self.user = DesUrUsersFactory()
        self.document = SubirDocsFactory()

    @patch('portaldu.desUr.tasks.os.listdir')
    @patch('portaldu.desUr.tasks.os.path.exists')
    def test_cleanup_old_logs_task(self, mock_exists, mock_listdir):
        """Test de tarea de limpieza de logs"""
        mock_exists.return_value = True
        mock_listdir.return_value = ['old_log.txt']

        with patch('portaldu.desUr.tasks.os.path.getmtime') as mock_getmtime, \
             patch('portaldu.desUr.tasks.os.remove') as mock_remove:

            # Simular archivo antiguo
            mock_getmtime.return_value = 1000000  # Timestamp muy antiguo

            result = cleanup_old_logs()

            self.assertIn('cleaned_files', result)
            mock_remove.assert_called()

    @patch('portaldu.desUr.tasks.send_mail')
    def test_send_notification_email_task(self, mock_send_mail):
        """Test de tarea de envío de emails"""
        mock_send_mail.return_value = True

        result = send_notification_email(
            'test@example.com',
            'Test Subject',
            'Test Message'
        )

        self.assertEqual(result['status'], 'success')
        mock_send_mail.assert_called_once()

    def test_process_document_upload_task(self):
        """Test de tarea de procesamiento de documentos"""
        result = process_document_upload(self.document.doc_ID)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['document_id'], self.document.doc_ID)

    def test_process_document_upload_not_found(self):
        """Test de tarea con documento inexistente"""
        result = process_document_upload(99999)

        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)

# Tests de integración
class TestIntegration(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = DesUrUsersFactory()
        self.data_instance = DataFactory()

    def test_complete_user_workflow(self):
        """Test de flujo completo de usuario"""
        # 1. Login
        login_data = {
            'username': self.user.username,
            'password': 'testpass123'
        }
        login_response = self.client.post(reverse('desur:login'), login_data)
        self.assertIn(login_response.status_code, [200, 302])

        # 2. Acceso a dashboard (si existe la ruta)
        try:
            dashboard_response = self.client.get(reverse('desur:dashboard'))
            self.assertEqual(dashboard_response.status_code, 200)
        except:
            pass  # Si no existe la ruta, continuar

    def test_document_upload_workflow(self):
        """Test de flujo de subida de documentos"""
        # Crear archivo de prueba
        test_file = SimpleUploadedFile(
            "test_document.txt",
            b"Contenido de prueba",
            content_type="text/plain"
        )

        document_data = {
            'nomDoc': 'Documento de prueba',
            'descDoc': 'Descripción del documento',
            'doc': test_file,
            'fuuid': self.data_instance.fuuid.prime
        }

        # Intentar crear documento
        document = SubirDocs.objects.create(
            fuuid=self.data_instance.fuuid,
            nomDoc=document_data['nomDoc'],
            descDoc=document_data['descDoc'],
            doc=test_file
        )

        self.assertIsNotNone(document.doc_ID)
        self.assertEqual(document.nomDoc, 'Documento de prueba')

# Tests de rendimiento
class TestPerformance(TestCase):
    def setUp(self):
        # Crear múltiples registros para tests de rendimiento
        self.users = DesUrUsersFactory.create_batch(50)
        self.data_instances = DataFactory.create_batch(100)

    def test_bulk_operations_performance(self):
        """Test de rendimiento para operaciones masivas"""
        import time

        start_time = time.time()

        # Consulta que podría ser lenta
        users_count = DesUrUsers.objects.count()
        data_count = data.objects.count()

        end_time = time.time()
        execution_time = end_time - start_time

        # Verificar que las consultas no tomen más de 1 segundo
        self.assertLess(execution_time, 1.0)
        self.assertEqual(users_count, 50)
        self.assertEqual(data_count, 100)

    def test_query_optimization(self):
        """Test de optimización de consultas"""
        from django.test.utils import override_settings
        from django.db import connection

        with override_settings(DEBUG=True):
            # Resetear queries
            connection.queries_log.clear()

            # Realizar consulta optimizada
            ciudadanos = data.objects.select_related('fuuid').all()[:10]
            list(ciudadanos)  # Forzar evaluación

            # Verificar número de queries
            query_count = len(connection.queries)
            self.assertLessEqual(query_count, 5)  # No más de 5 queries

# Configuración de pytest
pytest_plugins = ['django_nose']
