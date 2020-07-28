from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .serializers import PostSerializer


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'group.html', {'page': page, 'paginator': paginator, 'group': group})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    post_count = author.posts.count()

    form = CommentForm()

    return render(
        request,
        'post.html',
        {'post': post,
         'author': author,
         'post_count': post_count,
         'form': form
         }
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = author.posts.count()

    following = request.user.is_authenticated and\
                Follow.objects.filter(author=author, user=request.user).exists()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(
        request,
        'profile.html',
        {'page': page,
         'paginator': paginator,
         'author': author,
         'post_count': post_count,
         'following': following,
         'subscribe': True
         }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')

    return render(request, 'new.html', {'form': form})


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    post_url = reverse('post', args=(post.author, post.id))

    if post.author != request.user:
        return redirect(post_url)

    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if form.is_valid():
        post.save()
        return redirect(post_url)

    return render(request, 'new.html', {'form': form, 'post': post})


def post_delete(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    profile_url = reverse('profile', args=(post.author.username,))

    if post.author != request.user:
        return redirect('index')

    if post:
        post.delete()

    return redirect(profile_url)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    post_url = reverse('post', args=(post.author.username, post.id))

    if request.method == 'POST' and form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()

    return redirect(post_url)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    profile_url = reverse('profile', args=(author.username,))

    if author==user or Follow.objects.filter(user=user, author=author).exists():
        return redirect(profile_url)

    follow = Follow.objects.create(user=user, author=author)
    return redirect(profile_url)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    profile_url = reverse('profile', args=(author.username,))

    follow = Follow.objects.filter(user=user, author=author)
    if follow.exists():
        follow.delete()

    return redirect(profile_url)


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@api_view(['GET', 'POST'])
def api_posts(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUL', 'PATCH', 'DELETE'])
def api_posts_detail(request, id):
    post = Post.objects.get(id=id)
    if request.method == 'GET':
        serializer = PostSerializer(post)
        return Response(serializer.data)
    elif request.method == 'PUT' or request.method == 'PATCH':
        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)