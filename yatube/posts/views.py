
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
# from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def my_paginator(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# @cache_page(20)
def index(request):
    post_list = Post.objects.select_related('group', 'author')
    context = {'page_obj': my_paginator(request, post_list)}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    context = {'group': group, 'page_obj': my_paginator(request, post_list)}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.select_related('group', 'author')
    follow = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(user=request.user, author=user).exists()
    context = {
        'author': user,
        'page_obj': my_paginator(request, post_list),
        'following': follow,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'is_edit': True}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_list = Follow.objects.filter(user=request.user)
    post_list = Post.objects.filter(author__in=follow_list.values('author'))
    context = {'page_obj': my_paginator(request, post_list)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.username == username or Follow.objects.filter(
            user=request.user, author=author).exists():
        return profile(request, username)
    follow = Follow()
    follow.user = request.user
    follow.author = author
    follow.save()
    post_list = author.posts.select_related('group', 'author')
    context = {
        'author': author,
        'page_obj': my_paginator(request, post_list),
        'following': True
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    post_list = author.posts.select_related('group', 'author')
    context = {
        'author': author,
        'page_obj': my_paginator(request, post_list),
        'following': False
    }
    return render(request, 'posts/profile.html', context)
