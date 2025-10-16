"""
Comando de gestión para verificar y corregir contraseñas en el sistema unificado
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Verifica y corrige contraseñas hasheadas en el sistema unificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-passwords',
            action='store_true',
            help='Corrige contraseñas que no estén hasheadas correctamente',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula las correcciones sin realizar cambios reales',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Verifica solo un usuario específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_passwords = options['fix_passwords']
        username_filter = options['username']

        self.stdout.write(
            self.style.SUCCESS('=== VERIFICACIÓN DE CONTRASEÑAS ===')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo DRY-RUN: No se realizarán cambios reales')
            )

        # Obtener usuarios a verificar
        users = User.objects.all()
        if username_filter:
            users = users.filter(username=username_filter)
            if not users.exists():
                raise CommandError(f'Usuario "{username_filter}" no encontrado')

        total_users = users.count()
        self.stdout.write(f'Total de usuarios a verificar: {total_users}')

        valid_passwords = 0
        invalid_passwords = 0
        fixed_passwords = 0
        errors = 0

        with transaction.atomic():
            for user in users:
                try:
                    # Verificar si la contraseña está hasheada correctamente
                    password = user.password

                    # Las contraseñas hasheadas de Django empiezan con el algoritmo
                    if password.startswith(('pbkdf2_', 'bcrypt', 'argon2')):
                        valid_passwords += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {user.username}: Contraseña correctamente hasheada')
                        )
                    else:
                        invalid_passwords += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ {user.username}: Contraseña NO hasheada correctamente')
                        )

                        if fix_passwords:
                            if not dry_run:
                                # Si la contraseña parece ser texto plano, hashearla
                                if len(password) < 50:  # Las hasheadas son mucho más largas
                                    user.set_password(password)
                                    user.save()
                                    fixed_passwords += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f'✓ {user.username}: Contraseña corregida')
                                    )
                                else:
                                    # Podría ser un hash de otro formato, intentar con make_password
                                    user.password = make_password(password)
                                    user.save()
                                    fixed_passwords += 1
                                    self.stdout.write(
                                        self.style.WARNING(f'⚠ {user.username}: Contraseña re-hasheada')
                                    )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(f'⚠ {user.username}: Se corregiría en ejecución real')
                                )

                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'ERROR: {user.username} - {str(e)}')
                    )

        # Resumen final
        self.stdout.write('\n=== RESUMEN DE VERIFICACIÓN ===')
        self.stdout.write(f'Total verificados: {total_users}')
        self.stdout.write(
            self.style.SUCCESS(f'Contraseñas válidas: {valid_passwords}')
        )
        self.stdout.write(
            self.style.ERROR(f'Contraseñas inválidas: {invalid_passwords}')
        )

        if fix_passwords:
            self.stdout.write(
                self.style.SUCCESS(f'Contraseñas corregidas: {fixed_passwords}')
            )

        self.stdout.write(
            self.style.ERROR(f'Errores: {errors}')
        )

        if dry_run and fix_passwords:
            self.stdout.write(
                self.style.WARNING('NOTA: Fue una simulación, no se realizaron cambios reales')
            )

        # Realizar pruebas adicionales de seguridad
        self._security_checks()

    def _security_checks(self):
        """Realiza verificaciones adicionales de seguridad"""
        self.stdout.write('\n=== VERIFICACIONES DE SEGURIDAD ===')

        # Verificar usuarios duplicados por email
        from django.db.models import Count
        duplicated_emails = User.objects.values('email').annotate(
            count=Count('email')
        ).filter(count__gt=1)

        if duplicated_emails.exists():
            self.stdout.write(
                self.style.ERROR('¡ADVERTENCIA! Se encontraron emails duplicados:')
            )
            for dup in duplicated_emails:
                users_with_email = User.objects.filter(email=dup['email'])
                usernames = [u.username for u in users_with_email]
                self.stdout.write(f"  Email {dup['email']}: {usernames}")
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ No se encontraron emails duplicados')
            )

        # Verificar usuarios sin rol asignado
        users_without_role = User.objects.filter(rol='').count()
        if users_without_role > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠ {users_without_role} usuarios sin rol asignado')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ Todos los usuarios tienen rol asignado')
            )

        # Verificar usuarios inactivos
        inactive_users = User.objects.filter(is_active=False).count()
        self.stdout.write(f'ℹ {inactive_users} usuarios inactivos encontrados')

        # Verificar superusuarios
        superusers = User.objects.filter(is_superuser=True).count()
        self.stdout.write(f'ℹ {superusers} superusuarios encontrados')

        self.stdout.write(
            self.style.SUCCESS('Verificaciones de seguridad completadas')
        )
