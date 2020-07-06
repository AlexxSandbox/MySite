from io import BytesIO
from PIL import Image

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from .models import User, Post, Group, Follow, Comment


DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache',}}


class AuthUserPostView(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='12345')
        self.client.force_login(self.user)

        self.group = Group.objects.create(title='test_group', slug='test_group', description='test_group')

    def test_create_new_user_and_profile(self):
        resp = self.client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'profile.html')

    def test_logged_user_make_create_post(self):
        text = 'text for post'
        self.client.post(reverse('new_post'), data={'group': self.group.id, 'text': text}, follow=True)
        post = Post.objects.first()
        self.assertEquals(Post.objects.count(), 1)
        self.assertEquals(post.author, self.user)
        self.assertEquals(post.group, self.group)
        self.assertEquals(post.text, text)

    def test_view_post_on_all_templates(self):
        text = 'text for post'
        self.post = Post.objects.create(author=self.user, group=self.group, text=text)

        urls = [reverse('index'),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('post', kwargs={'username': self.user.username, 'post_id': self.post.id}),
                reverse('group', kwargs={'slug': self.group.slug})
                ]

        for url in urls:
            with self.subTest(url=url):
                self.check_post_on_templates(url=url, author=self.user, group=self.group, text=text)

    def test_logged_user_edit_post(self):
        text = 'text for post'
        new_text = 'new text'
        new_group = Group.objects.create(title='new_group', slug='new_group', description='new_group')
        self.post = Post.objects.create(author=self.user, group=self.group, text=text)

        self.client.post(
            reverse('post_edit', kwargs={'username': self.user, 'post_id': self.post.id}),
            data={'group': new_group.id, 'text': new_text}, follow=True)
        resp_old_group = self.client.get(reverse('group', kwargs={'slug': self.group}))
        self.assertEquals(resp_old_group.context['paginator'].count, 0)

        urls = [reverse('index'),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('post', kwargs={'username': self.user.username, 'post_id': self.post.id}),
                reverse('group', kwargs={'slug': new_group.slug})
                ]

        for url in urls:
            with self.subTest(url=url):
                self.check_post_on_templates(url=url, author=self.user, group=new_group, text=new_text)

    def check_post_on_templates(self, url, author, group, text):
        resp = self.client.get(url)
        if 'paginator' in resp.context:
            self.assertEquals(resp.context['paginator'].count, 1)
            post = resp.context['page'][0]
        else:
            post = resp.context['post']
        self.assertEquals(post.text, text)
        self.assertEquals(post.author, author)
        self.assertEquals(post.group, group)

    def test_redirect_if_not_logged_user_try_create_post(self):
        self.client.logout()
        resp = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(resp, '/auth/login/?next=/new/')

    def test_error_404(self):
        resp = self.client.get('/404/')
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'misc/404.html')

    @override_settings(CACHES=DUMMY_CACHE)
    def test_tag_on_post_template(self):
        io_image = BytesIO()
        generated_image = Image.new(mode='RGBA', size=(100, 100))
        generated_image.save(io_image, 'png')
        io_image.seek(0)

        data = {'group': self.group.id, 'text': 'new_text', 'image': ImageFile(io_image, 'image.png')}
        self.client.post(reverse('new_post'), data=data, follow=True)

        urls = [reverse('index'),
                reverse('post', kwargs={'username': self.user.username, 'post_id': 1}),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('group', kwargs={'slug': self.group.slug})
                ]

        for url in urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertContains(resp, '<img')

    def test_form_image_field_validation(self):
        txt_file = SimpleUploadedFile('file.txt', b'text_file')
        resp = self.client.post(reverse('new_post'), data={'group': self.group.id, 'image': txt_file}, follow=True)
        error = 'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'
        self.assertFormError(resp, 'form', 'image', error)

    def test_cache_index_posts(self):
        text_new_post = 'text for post'
        text_after_edit = 'new text'

        post = Post.objects.create(author=self.user, group=self.group, text=text_new_post)
        self.check_version_template_in_cache(text=text_new_post)

        self.client.post(
                reverse('post_edit',
                        kwargs={'username': self.user, 'post_id': post.id}),
                        data={'group': self.group.id, 'text': text_after_edit},
                        follow=True)
        self.check_version_template_in_cache(text=text_new_post)

        response = self.client.get(reverse('index'))
        key = make_template_fragment_key('index_page', [response.context['page'].number])
        cache.delete(key)
        self.check_version_template_in_cache(text=text_after_edit)

    def check_version_template_in_cache(self, text):
        resp = self.client.get(reverse('index'))
        self.assertContains(resp, text)


class FollowAndCommentView(TestCase):

    def setUp(self):
        self.client = Client()

        self.user_follower = User.objects.create_user(username='follower', password='12345')
        self.client.force_login(self.user_follower)

        self.user_wo_subscribe = User.objects.create_user(username='user_wo_subscribe', password='12345')
        self.user_for_subscribe = User.objects.create_user(username='user_for_subscribe', password='12345')

        self.group = Group.objects.create(title='test_group', slug='test_group', description='test_group')

    def test_user_subscribe_and_unsubscribe_author(self):
        self.client.post(reverse('profile_follow', kwargs={'username': self.user_for_subscribe}))
        self.assertEquals(Follow.objects.count(), 1)

        subscribed_author = Follow.objects.get(user=self.user_follower)
        self.assertEquals(subscribed_author.author, self.user_for_subscribe)

    def test_user_unsubscribe_author(self):
        self.client.post(reverse('profile_follow', kwargs={'username': self.user_for_subscribe}))
        self.assertEquals(Follow.objects.count(), 1)

        self.client.post(reverse('profile_unfollow', kwargs={'username': self.user_for_subscribe}))
        self.assertEquals(Follow.objects.count(), 0)

    @override_settings(CACHES=DUMMY_CACHE)
    def test_posts_subscribed_user(self):
        text = 'following_text'
        self.client.force_login(self.user_for_subscribe)
        self.client.post(reverse('new_post'), data={'group': self.group.id, 'text': text}, follow=True)

        self.client.force_login(self.user_follower)
        self.client.post(reverse('profile_follow', kwargs={'username': self.user_for_subscribe}))
        resp_subscribed = self.client.get(reverse('follow_index'))
        self.assertEquals(resp_subscribed.context['paginator'].count, 1)
        self.assertContains(resp_subscribed, text)

    def test_nonsubscribed_user_posts(self):
        text = 'following_text'
        self.client.force_login(self.user_for_subscribe)
        self.client.post(reverse('new_post'), data={'group': self.group.id, 'text': text}, follow=True)

        self.client.force_login(self.user_wo_subscribe)
        resp_nonsubscribed = self.client.get(reverse('follow_index'))
        self.assertEquals(resp_nonsubscribed.context['paginator'].count, 0)

    def test_subscribe_by_itself(self):
        resp_tag = self.client.get(reverse('profile', kwargs={'username': self.user_follower.username}))
        self.assertNotContains(resp_tag, 'Подписаться')
        self.assertNotContains(resp_tag, 'Отписаться')

    def test_auth_user_add_comment(self):
        text_comment = 'text for comment'
        text = 'following_text'
        self.client.force_login(self.user_for_subscribe)
        self.client.post(reverse('new_post'), data={'group': self.group.id, 'text': text}, follow=True)

        self.client.force_login(self.user_follower)
        post = Post.objects.get(author=self.user_for_subscribe)
        self.client.post(
            reverse('add_comment',
                    kwargs={'username': self.user_for_subscribe, 'post_id': post.id}),
                    data={'text': text_comment}, follow=True)

        comment = Comment.objects.get(author=self.user_follower)

        self.assertEquals(Comment.objects.count(), 1)
        self.assertEquals(comment.text, text_comment)
        self.assertEquals(comment.post.text, post.text)

        resp = self.client.get(reverse('post', kwargs={'username': self.user_for_subscribe, 'post_id': post.id}))
        self.assertEquals(resp.context['comments'][0].text, text_comment)

    def test_non_auth_user_add_comment(self):
        text = 'following_text'
        self.client.force_login(self.user_for_subscribe)
        self.client.post(reverse('new_post'), data={'group': self.group.id, 'text': text}, follow=True)

        self.client.logout()
        text_comment = 'text for comment'
        post = Post.objects.get(author=self.user_for_subscribe)
        self.client.post(
            reverse('add_comment',
                    kwargs={'username': self.user_for_subscribe, 'post_id': post.id}),
                    data={'text': text_comment}, follow=True)

        comments_count = Comment.objects.count()
        self.assertEquals(comments_count, 0)
