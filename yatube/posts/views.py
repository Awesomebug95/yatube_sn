from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseRedirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def paginator_view(request, post_list):
    paginator = Paginator(post_list, settings.PAGINATOR_CONST)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


# @cache_page(15, key_prefix='index_page')
def index(request):
    return render(request, "posts/index.html", {
        "page_obj": paginator_view(request, Post.objects.all())
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, "posts/group_list.html", {
        "group": group,
        "page_obj": paginator_view(request, group.posts.all()),
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and user.following.exists()
    return render(request, "posts/profile.html", {
        "author": user,
        "page_obj": paginator_view(request, user.posts.all()),
        'following': following,
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    return render(request, "posts/post_detail.html", {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, "posts/create_post.html", {"form": form})
    form.instance.author = request.user
    form.save()
    return redirect("posts:profile", username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author.id != request.user.id:
        return redirect("posts:index")
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post.id)
    return render(request, "posts/create_post.html", {
        "form": form,
        "is_edit": True,
        "post": post,
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/post_detail.html', {
            form: 'form',
            post: 'post',
        })
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = request.user.follower.values_list('author', flat=True)
    page_obj = paginator_view(request, Post.objects.filter(
        author__id__in=authors
    ))
    return render(request, 'posts/follow.html', {
        'page_obj': page_obj,
    })


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:profile', username)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))