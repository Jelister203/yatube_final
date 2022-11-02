from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_200(self):
        # Все 200 для гостей
        urls_templates_names_guests = {
            '/auth/signup/': None,
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': None,
        }
        for address, template in urls_templates_names_guests.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                if template:
                    self.assertTemplateUsed(response, template)

    def test_404(self):
        fake_response = self.guest.get('auth/how_to_test_urls/')
        self.assertEqual(fake_response.status_code, HTTPStatus.NOT_FOUND)
