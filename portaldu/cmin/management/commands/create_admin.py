"""
Comando de gestión de Django para crear usuario administrador
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea un usuario administrador con permisos completos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Nombre de usuario del administrador (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@civitas.com',
            help='Email del administrador',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Contraseña temporal del administrador (default: admin123)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Actualiza el usuario si ya existe',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS('=== CREACIÓN DE USUARIO ADMINISTRADOR ===')
        )

        # Verificar si ya existe
        try:
            existing_user = User.objects.get(username=username)

            if not force:
                self.stdout.write(
                    self.style.WARNING(f'El usuario "{username}" ya existe.')
                )
                self.stdout.write('Usa --force para actualizar sus permisos.')
                return

            # Actualizar usuario existente
            existing_user.is_superuser = True
            existing_user.is_staff = True
            existing_user.is_active = True
            existing_user.rol = 'administrador'
            existing_user.email = email
            existing_user.set_password(password)
            existing_user.save()

            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario "{username}" actualizado con permisos de administrador')
            )

        except User.DoesNotExist:
            # Crear nuevo usuario
            admin_user = User.objects.create(
                username=username,
                email=email,
                first_name='Administrador',
                last_name='Sistema',
                is_superuser=True,
                is_staff=True,
                is_active=True,
                rol='administrador'
            )

            admin_user.set_password(password)
            admin_user.save()

            self.stdout.write(
                self.style.SUCCESS(f'🎉 Usuario administrador "{username}" creado exitosamente!')
            )

        # Verificar permisos
        user = User.objects.get(username=username)

        self.stdout.write('\n=== VERIFICACIÓN DE PERMISOS ===')
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Rol: {user.rol}')
        self.stdout.write(f'Superusuario: {"Sí" if user.is_superuser else "No"}')
        self.stdout.write(f'Staff: {"Sí" if user.is_staff else "No"}')
        self.stdout.write(f'Activo: {"Sí" if user.is_active else "No"}')

        # Verificar métodos específicos
        self.stdout.write(f'Acceso CMIN: {"Sí" if user.has_cmin_access() else "No"}')
        self.stdout.write(f'Acceso DesUr: {"Sí" if user.has_desur_access() else "No"}')
        self.stdout.write(f'Puede crear usuarios: {"Sí" if user.can_create_users() else "No"}')

        self.stdout.write('\n=== CREDENCIALES DE ACCESO ===')
        self.stdout.write(f'Usuario: {username}')
        self.stdout.write(f'Contraseña: {password}')

        self.stdout.write('\n=== INSTRUCCIONES ===')
        self.stdout.write('1. Inicia sesión en el sistema')
        self.stdout.write('2. CAMBIA LA CONTRASEÑA inmediatamente por seguridad')
        self.stdout.write('3. Como administrador puedes:')
        self.stdout.write('   - Crear otros usuarios desde el panel de CMIN')
        self.stdout.write('   - Acceder a todas las secciones del sistema')
        self.stdout.write('   - Gestionar tanto CMIN como DesUr')
        self.stdout.write('   - Administrar usuarios y permisos')

        self.stdout.write(
            self.style.SUCCESS('\n✅ Usuario administrador listo para usar!')
        )
