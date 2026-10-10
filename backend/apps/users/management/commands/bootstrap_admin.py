import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from apps.users.models import Role


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create or reset one explicitly identified CareFlow administrator. "
        "Use only with the intended Render PostgreSQL external DATABASE_URL."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Exact email address for the admin account.")
        parser.add_argument("--username", required=True, help="Exact username for the admin account.")
        parser.add_argument(
            "--confirm-database-host",
            required=True,
            help="Must exactly match the database host shown in Render's external connection URL.",
        )

    def handle(self, *args, **options):
        database = connections["default"]
        configured_host = database.settings_dict.get("HOST", "").strip().lower()
        confirmed_host = options["confirm_database_host"].strip().lower()
        if database.vendor != "postgresql" or not configured_host:
            raise CommandError("Refusing to run: the default database is not a configured PostgreSQL database.")
        if confirmed_host != configured_host:
            raise CommandError("Database host confirmation does not match the configured database host.")

        email = options["email"].strip()
        username = options["username"].strip()
        if not email or not username:
            raise CommandError("Email and username must not be blank.")

        first_password = getpass.getpass("New administrator password (input hidden): ")
        second_password = getpass.getpass("Confirm administrator password (input hidden): ")
        if first_password != second_password:
            raise CommandError("Passwords do not match; no account changes were made.")
        if len(first_password) < 14:
            raise CommandError("Password must be at least 14 characters; no account changes were made.")

        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=email).first()
            username_owner = User.objects.filter(username__iexact=username)
            if user:
                username_owner = username_owner.exclude(pk=user.pk)
                if user.username.casefold() != username.casefold():
                    raise CommandError(
                        "That email already belongs to a different username. Refusing to alter another account."
                    )
            if username_owner.exists():
                raise CommandError("That username belongs to a different account; no changes were made.")

            candidate = user or User(email=email, username=username, role=Role.ADMIN)
            try:
                validate_password(first_password, user=candidate)
            except ValidationError as exc:
                raise CommandError("Password rejected by Django's configured password validators.") from exc

            created = user is None
            if created:
                user = candidate
            user.role = Role.ADMIN
            user.is_active = True
            user.is_active_staff = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(first_password)
            try:
                user.full_clean()
            except ValidationError as exc:
                raise CommandError("Administrator email or account fields are invalid.") from exc
            user.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} administrator account for {email}. Password was not displayed."))
