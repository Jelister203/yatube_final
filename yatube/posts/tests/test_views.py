from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from posts.models import Group, Post, Comment, Follow
from django.core.files.uploadedfile import SimpleUploadedFile

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

    def test_404_custom_page(self):
        response = self.auth_client.get('un-existing/page/')
        self.assertTemplateUsed(response, 'core/404.html')


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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Пост',
            author=cls.author,
            group=cls.group,
            image=uploaded,
        )
        cls.post2 = Post.objects.create(
            text='Пост без группы',
            author=cls.author2,
        )
        Comment.objects.create(
            text='Комментарий',
            author=cls.author,
            post=cls.post
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.author)
        self.auth_client2 = Client()
        self.auth_client2.force_login(self.author2)

    def test_correct_context_follow(self):
        subs0 = Follow.objects.filter(user=self.author)
        self.auth_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author2.username}
            )
        )
        subs1 = Follow.objects.filter(user=self.author)
        self.auth_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author2.username}
            )
        )
        subs2 = Follow.objects.filter(user=self.author)

        self.assertNotEqual(subs0, subs1)
        self.assertEqual(subs0, subs2)

    def test_correct_context_unique_follow(self):
        self.auth_client.post(
            reverse(  # юзер1 подписывается на юезра2
                'posts:profile_follow',
                kwargs={'username': self.author2.username}
            )
        )
        self.auth_client2.post(
            reverse(  # юзер2 подписывается на юезра1
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        form_data = {'text': 'Text'}
        self.auth_client2.post(  # юзер2 пишет пост
            reverse('posts:post_create'), data=form_data, follow=True
        )
        response1 = self.auth_client.get(reverse('posts:index'))
        post2 = response1.context['page_obj'][0]  # сохраняем пост юзера2

        form_data = {'text': 'Текст'}
        self.auth_client.post(  # юзер1 пишет пост
            reverse('posts:post_create'), data=form_data, follow=True
        )
        response1 = self.auth_client.get(reverse('posts:index'))
        post1 = response1.context['page_obj'][0]  # сохраняем пост юзера1

        response1 = self.auth_client.get(reverse('posts:follow_index'))
        post_follow_2 = response1.context['page_obj'][0]
        #  юзер1 смотрит последний пост юзера2
        response2 = self.auth_client2.get(reverse('posts:follow_index'))
        post_follow_1 = response2.context['page_obj'][0]
        #  юзер1 смотрит последний пост юзера2
        self.assertEqual(post2, post_follow_2)
        self.assertEqual(post1, post_follow_1)

    def test_correct_context_index(self):
        response = self.auth_client.get(reverse('posts:index'))

        objects = response.context['page_obj']
        self.assertEqual(len(objects), 2)

        first_obj = objects[1]
        post_author_0 = first_obj.author
        post_group_0 = first_obj.group
        post_text_0 = first_obj.text
        post_image_0 = first_obj.image
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_group_0.title, 'Группа')
        self.assertEqual(post_text_0, 'Пост')
        self.assertEqual(post_image_0, 'posts/small.gif')

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
        post_image_0 = first_obj.image
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_correct_context_profile(self):
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        objects = response.context['page_obj']

        self.assertEqual(response.context['author'], self.author)

        first_obj = objects[0]
        post_author_0 = first_obj.author
        post_text_0 = first_obj.text
        post_image_0 = first_obj.image
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_correct_context_post_detail(self):
        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

        first_obj = response.context['post']
        post_author_0 = first_obj.author
        post_text_0 = first_obj.text
        post_image_0 = first_obj.image
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_text_0, 'Пост')
        self.assertEqual(post_image_0, 'posts/small.gif')

        context = response.context['comments'][0]
        comm_text = context.text
        comm_author = context.author
        self.assertEqual(comm_text, 'Комментарий')
        self.assertEqual(comm_author, self.author)

    def test_correct_context_post_create(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
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

    def test_cache_index(self):
        response = self.auth_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Новый пост',
            author=self.author2,
        )
        response_old = self.auth_client.get(reverse('posts:index'))
        posts_old = response_old.content
        self.assertEqual(posts_old, posts)
        cache.clear()
        response_new = self.auth_client.get(reverse('posts:index'))
        posts_new = response_new.content
        self.assertNotEqual(posts_old, posts_new)


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
