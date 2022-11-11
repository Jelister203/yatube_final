import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super(PostPagesTests, cls).tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.author)
        self.guest = Client()

    def test_create_post(self):
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Text',
            'image': uploaded,
        }
        self.client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        new_post = Post.objects.get(pk=self.post.pk + 1)
        self.assertEqual(new_post.text, 'Text')
        self.assertEqual(new_post.author, self.author)
        self.assertEqual(new_post.group, None)
        self.assertEqual(new_post.image, 'posts/small.gif')

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

    def test_user_comment(self):
        comm_count = Comment.objects.count()
        post_id = self.post.pk
        form_data = {
            'text': 'Обычный комментарий',
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comm_count + 1)
        self.assertEqual(Comment.objects.get(pk=1).text, "Обычный комментарий")

    def test_guest_comment(self):
        comm_count = Comment.objects.count()
        post_id = self.post.pk
        form_data = {
            'text': 'Обычный комментарий',
        }
        self.guest.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comm_count)
