from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest = Client()
        self.OK: int = HTTPStatus.OK
        self.NOT_FOUND = HTTPStatus.NOT_FOUND

    def test_200(self):
        about_response = self.guest.get('/about/author/')
        tech_response = self.guest.get('/about/tech/')
        self.assertEqual(about_response.status_code, self.OK)
        self.assertEqual(tech_response.status_code, self.OK)

    def test_404(self):
        fake_response = self.guest.get('about/how_to_test_urls/')
        self.assertEqual(fake_response.status_code, self.NOT_FOUND)
