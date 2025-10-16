"""
Comando de gestión de Django para migrar usuarios de DesUr al sistema unificado
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from portaldu.desUr.models import DesUrUsers
from portaldu.desUr.auth import DesUrAuthBackend

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Migra usuarios de DesUrUsers al modelo unificado Users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin realizar cambios reales',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la migración incluso si hay conflictos',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Migra solo un usuario específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        username_filter = options['username']

        self.stdout.write(
            self.style.SUCCESS('=== MIGRACIÓN DE USUARIOS DESUR AL SISTEMA UNIFICADO ===')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo DRY-RUN: No se realizarán cambios reales')
            )

        # Obtener usuarios a migrar
        desur_users = DesUrUsers.objects.all()
        if username_filter:
            desur_users = desur_users.filter(username=username_filter)
            if not desur_users.exists():
                raise CommandError(f'Usuario "{username_filter}" no encontrado en DesUrUsers')

        total_users = desur_users.count()
        self.stdout.write(f'Total de usuarios DesUr a procesar: {total_users}')

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for desur_user in desur_users:
                try:
                    # Verificar si ya existe en el modelo unificado
                    existing_user = User.objects.filter(username=desur_user.username).first()

                    if existing_user:
                        if not force:
                            self.stdout.write(
                                self.style.WARNING(f'OMITIDO: Usuario {desur_user.username} ya existe')
                            )
                            skipped_count += 1
                            continue
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'FORZANDO: Actualizando usuario existente {desur_user.username}')
                            )

                    # Verificar conflicto de email
                    email_conflict = User.objects.filter(email=desur_user.email).exclude(username=desur_user.username).first()
                    if email_conflict and not force:
                        self.stdout.write(
                            self.style.ERROR(f'CONFLICTO EMAIL: {desur_user.email} ya está en uso por {email_conflict.username}')
                        )
                        error_count += 1
                        continue

                    if not dry_run:
                        # Realizar la migración
                        if existing_user:
                            # Actualizar usuario existente
                            user = existing_user
                            user.email = desur_user.email
                            user.first_name = desur_user.first_name
                            user.last_name = desur_user.last_name
                            user.bday = desur_user.bday
                            if desur_user.foto:
                                user.foto = desur_user.foto
                            user.is_active = desur_user.is_active
                            if desur_user.date_joined:
                                user.date_joined = desur_user.date_joined
                            if desur_user.last_login:
                                user.last_login = desur_user.last_login
                            # Mantener la contraseña hasheada
                            user.password = desur_user.password
                            user.save()
                        else:
                            # Crear nuevo usuario
                            user = User.objects.create(
                                username=desur_user.username,
                                email=desur_user.email,
                                first_name=desur_user.first_name,
                                last_name=desur_user.last_name,
                                bday=desur_user.bday,
                                foto=desur_user.foto,
                                is_active=desur_user.is_active,
                                date_joined=desur_user.date_joined,
                                last_login=desur_user.last_login,
                                rol='campo'  # Los usuarios de DesUr son por defecto de campo
                            )
                            # Copiar la contraseña hasheada
                            user.password = desur_user.password
                            user.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'✓ MIGRADO: {desur_user.username} -> {desur_user.email}')
                    )
                    migrated_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'ERROR: {desur_user.username} - {str(e)}')
                    )
                    error_count += 1

        # Resumen final
        self.stdout.write('\n=== RESUMEN DE MIGRACIÓN ===')
        self.stdout.write(f'Total procesados: {total_users}')
        self.stdout.write(
            self.style.SUCCESS(f'Migrados exitosamente: {migrated_count}')
        )
        self.stdout.write(
            self.style.WARNING(f'Omitidos (ya existían): {skipped_count}')
        )
        self.stdout.write(
            self.style.ERROR(f'Errores: {error_count}')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('NOTA: Fue una simulación, no se realizaron cambios reales')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Migración completada')
            )

        # Verificar integridad después de la migración
        if not dry_run and migrated_count > 0:
            self.stdout.write('\n=== VERIFICACIÓN DE INTEGRIDAD ===')
            self._verify_migration()

    def _verify_migration(self):
        """Verifica la integridad de la migración"""
        # Verificar que no hay duplicados de email
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

        # Verificar que las contraseñas están hasheadas
        invalid_passwords = User.objects.exclude(
            password__startswith='pbkdf2_'
        ).exclude(
            password__startswith='bcrypt'
        ).exclude(
            password__startswith='argon2'
        ).count()

        if invalid_passwords > 0:
            self.stdout.write(
                self.style.ERROR(f'¡ADVERTENCIA! {invalid_passwords} usuarios con contraseñas no hasheadas')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ Todas las contraseñas están correctamente hasheadas')
            )

        self.stdout.write(
            self.style.SUCCESS('Verificación de integridad completada')
        )
