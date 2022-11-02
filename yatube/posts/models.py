from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    class Meta:
        verbose_name = 'Группы'

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.title}'


class Post(models.Model):
    class Meta:
        verbose_name = 'Посты'
        ordering = ['-pub_date']

    text = models.TextField(
        'Текст поста', max_length=5000, help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='posts',
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        verbose_name='Группа',
        related_name='posts',
        null=True,
        on_delete=models.SET_NULL,
        help_text=('Группа, к которой будет ' 'относиться пост'),
    )

    def __str__(self):
        return self.text[:15]
