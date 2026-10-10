import secrets
from unittest.mock import PropertyMock, patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import connections
from django.test import TestCase

User = get_user_model()


class BootstrapAdminCommandTests(TestCase):
    def setUp(self):
        self.database = connections["default"]
        self.password = f"{secrets.token_urlsafe(24)}aA1!"
        self.previous_password = f"{secrets.token_urlsafe(24)}bB2!"
        self.original_host = self.database.settings_dict.get("HOST", "")
        self.database.settings_dict["HOST"] = "render-db.example"
        self.vendor_patch = patch.object(
            type(self.database), "vendor", new_callable=PropertyMock, return_value="postgresql"
        )
        self.vendor_patch.start()
        self.addCleanup(self.vendor_patch.stop)
        self.addCleanup(self._restore_database_host)

    def _restore_database_host(self):
        self.database.settings_dict["HOST"] = self.original_host

    def run_bootstrap(self, email="admin@example.com", username="site-admin", password=None):
        password = password or self.password
        with patch(
            "apps.users.management.commands.bootstrap_admin.getpass.getpass",
            side_effect=[password, password],
        ):
            call_command(
                "bootstrap_admin",
                email=email,
                username=username,
                confirm_database_host="render-db.example",
                verbosity=0,
            )

    def test_creates_admin_with_hashed_password(self):
        self.run_bootstrap()
        user = User.objects.get(email="admin@example.com")
        self.assertEqual(user.role, "ADMIN")
        self.assertTrue(user.is_active and user.is_active_staff and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password(self.password))

    def test_rerun_updates_only_matching_admin(self):
        existing = User.objects.create_user(
            username="site-admin", email="admin@example.com", password=self.previous_password, role="DOCTOR"
        )
        self.run_bootstrap()
        existing.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(existing.role, "ADMIN")
        self.assertTrue(existing.is_superuser)
        self.assertTrue(existing.check_password(self.password))

    def test_refuses_email_owned_by_different_username(self):
        User.objects.create_user(
            username="someone-else", email="admin@example.com", password=self.previous_password, role="DOCTOR"
        )
        with self.assertRaises(CommandError):
            self.run_bootstrap()
        self.assertEqual(User.objects.get(email="admin@example.com").role, "DOCTOR")

    def test_refuses_wrong_database_host_before_prompting(self):
        with self.assertRaises(CommandError), patch(
            "apps.users.management.commands.bootstrap_admin.getpass.getpass"
        ) as password_prompt:
            call_command(
                "bootstrap_admin",
                email="admin@example.com",
                username="site-admin",
                confirm_database_host="another-db.example",
            )
        password_prompt.assert_not_called()

    def test_refuses_short_password_without_creating_user(self):
        with self.assertRaises(CommandError):
            self.run_bootstrap(password="too-short")
        self.assertFalse(User.objects.exists())
