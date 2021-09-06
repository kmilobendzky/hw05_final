from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from yatube.settings import PAGINATOR_CONSTANT

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PAGINATOR_CONSTANT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, PAGINATOR_CONSTANT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj, }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    try:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    except TypeError:
        following = False
    post_list = author.posts.all()
    paginator = Paginator(post_list, PAGINATOR_CONSTANT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_count = post_list.count()
    context = {'author': author,
               'page_obj': page_obj,
               'post_count': post_count,
               'following': following,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    post_count = post.author.posts.count()
    context = {'post': post,
               'post_count': post_count,
               'form': form,
               'comments': comments,
               }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_post_creation = True
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post:profile', username=post.author)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_post_creation': is_post_creation})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.published_date = timezone.now()
            post.save()
        return redirect('post:post_detail', post_id=post.pk)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, PAGINATOR_CONSTANT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user == author:
        return redirect('post:profile', username=user.username)
    elif Follow.objects.filter(user=user, author=author).exists():
        return redirect('post:profile', username=user.username)
    else:
        Follow.objects.create(user=user, author=author)
        return redirect('post:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user == author:
        return redirect('post:profile', username=user.username)
    else:
        deleting_follow = Follow.objects.get(user=user, author=author)
        deleting_follow.delete()
        return redirect('post:profile', username=author.username)
