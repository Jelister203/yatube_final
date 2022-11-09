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
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='posts',
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        verbose_name='Группа',
        related_name='posts',
        null=True,
        on_delete=models.SET_NULL,
        help_text=('Группа, к которой будет '
                   'относиться пост')
    )

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    class Meta:
        verbose_name = 'Комменты'
        ordering = ['-created']
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='comments',
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        related_name='comments',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    class Meta:
        verbose_name = 'Подписки'
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Публицист',
        related_name='following',
        on_delete=models.CASCADE
    )
    
    def __str__(self):
        return f"Фоловер: {self.user}; Автор: {self.author}."
