from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest = Client()
        self.user = Client()
        self.user2 = Client()
        user = User.objects.create_user(username='Unknown')
        user2 = User.objects.create_user(username='Unknown2')
        self.user.force_login(user)
        self.user2.force_login(user2)
        self.post = Post.objects.create(
            text='Текст поста',
            author=user,
        )
        self.post2 = Post.objects.create(
            text='Текст поста',
            author=user2,
        )
        Group.objects.create(title='Группа', slug='slug', description='Группа')

    def test_unexisting_page(self):
        # Выбрасывает 404 при запросе на несуществующую страницу
        unexisting_page_response = self.guest.get('/unexisting_page/')
        self.assertEqual(
            unexisting_page_response.status_code, HTTPStatus.NOT_FOUND
        )

    def test_anonymous_post_create(self):
        # Редирект гостей на вход
        guest_create_response = self.guest.get('/create/')
        self.assertRedirects(
            guest_create_response, ('/auth/login/?next=/create/')
        )

    def test_anonymous_post_edit(self):
        guest_edit_response = self.guest.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(
            guest_edit_response,
            (f'/auth/login/?next=/posts/{self.post.pk}/edit/'),
        )

    def test_WrongAuthor_post_edit(self):
        # Редирект при попытке редактирования чужого поста
        user_edit_other_response = self.user.get(
            f'/posts/{self.post2.pk}/edit/'
        )
        self.assertRedirects(
            user_edit_other_response, (f'/posts/{self.post2.pk}/')
        )

    def test_user_access(self):
        # 200 для авторизированных юзеров
        urls_templates_names_users = {
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/Unknown/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in urls_templates_names_users.items():
            with self.subTest(address=address):
                response = self.user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_guest_access(self):
        # Все 200 для гостей
        urls_templates_names_guests = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/Unknown/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in urls_templates_names_guests.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
