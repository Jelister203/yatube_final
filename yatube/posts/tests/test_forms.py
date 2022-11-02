from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            text='Пост',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.author)
        self.guest = Client()

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Text',
        }
        self.client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        new_post = Post.objects.get(pk=self.post.pk + 1)
        self.assertEqual(new_post.text, 'Text')
        self.assertEqual(new_post.author, self.author)

    def test_edit_post(self):
        post_count = Post.objects.count()
        post_id = self.post.pk
        form_data = {
            'text': 'Пост с группой для теста',
            'group': self.group.pk,
        }
        self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(post_count, Post.objects.count())
        self.assertEqual(
            Post.objects.get(pk=self.post.pk).text, 'Пост с группой для теста'
        )

    def test_guest_create(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Text',
        }
        self.guest.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_guest_edit(self):
        post_count = Post.objects.count()
        post_id = self.post.pk
        form_data = {
            'text': 'Пост с группой для теста',
            'group': self.group.pk,
        }
        self.guest.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(post_count, Post.objects.count())
        self.assertEqual(Post.objects.get(pk=1).text, 'Пост')
