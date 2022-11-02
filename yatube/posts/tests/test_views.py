from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostTemplateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.author2 = User.objects.create(username='author2')
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
        cls.post2 = Post.objects.create(
            text='Пост без группы',
            author=cls.author2,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.author)

    def test_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'slug'})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile', kwargs={'username': 'author'})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PostContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.author2 = User.objects.create(username='author2')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание группы',
        )
        Post.objects.create(
            text='Пост',
            author=cls.author,
            group=cls.group,
        )
        Post.objects.create(
            text='Пост без группы',
            author=cls.author2,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.author)

    def test_correct_context_index(self):
        response = self.auth_client.get(reverse('posts:index'))

        objects = response.context['page_obj']
        self.assertEqual(len(objects), 2)

        first_obj = objects[1]
        post_author_0 = first_obj.author
        post_group_0 = first_obj.group
        post_text_0 = first_obj.text
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_group_0.title, 'Группа')
        self.assertEqual(post_text_0, 'Пост')

    def test_correct_context_group_list(self):
        response = self.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        )
        objects = response.context['page_obj']

        title_obj = response.context['group']
        self.assertEqual(title_obj, self.group)

        first_obj = objects[0]
        post_author_0 = first_obj.author
        post_text_0 = first_obj.text
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')

    def test_correct_context_profile(self):
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        objects = response.context['page_obj']

        self.assertEqual(response.context['author'], self.author)

        first_obj = objects[0]
        post_author_0 = first_obj.author
        post_text_0 = first_obj.text
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')

    def test_correct_context_post_detail(self):
        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )

        first_obj = response.context['post']
        post_author_0 = first_obj.author
        post_text_0 = first_obj.text
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')

    def test_correct_context_post_create(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correct_context_post_edit(self):
        response = self.auth_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        is_edit = response.context['is_edit']
        self.assertEqual(is_edit, True)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.author2 = User.objects.create(username='author2')
        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание группы',
        )
        Post.objects.create(
            text='Пост',
            author=cls.author,
            group=cls.group,
        )
        Post.objects.create(
            text='Пост без группы',
            author=cls.author2,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.author)

    def test_correct_context_profile(self):
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        objects = response.context['page_obj']
        self.assertEqual(len(objects), 1)

    def test_correct_context_group_list(self):
        response = self.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        )
        objects = response.context['page_obj']
        self.assertEqual(len(objects), 1)

    def test_correct_context_index(self):
        response = self.auth_client.get(reverse('posts:index'))
        objects = response.context['page_obj']
        self.assertEqual(len(objects), 2)
