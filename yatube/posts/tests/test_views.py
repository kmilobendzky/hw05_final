import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

from yatube.settings import PAGINATOR_CONSTANT

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='darkh01m')
        cls.user3 = User.objects.create_user(username='h3rringt0n')
        cls.test_group = Group.objects.create(
            title='yay', slug='yay', description='yay')
        cls.test_group2 = Group.objects.create(
            title='aya', slug='aya', description='aya')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.authorized_client3 = Client()
        cls.authorized_client3.force_login(cls.user3)
        cls.posts_data_list = []
        for i in range(15):
            created_post = Post.objects.create(
                text=f'Test post {i}.', author=cls.user, group=cls.test_group)
            cls.posts_data_list.append(created_post)
        cls.user3_post = Post.objects.create(
                text=f'Test post for following.', author=cls.user3, group=cls.test_group)
        cls.reverse_index = reverse('post:index')
        cls.reverse_group_list = reverse(
            'post:group_list',
            kwargs={'slug': TaskPagesTests.test_group.slug})
        cls.reverse_group_list2 = reverse(
            'post:group_list',
            kwargs={'slug': TaskPagesTests.test_group2.slug})
        cls.reverse_profile = reverse(
            'post:profile',
            kwargs={'username': TaskPagesTests.user.username})
        cls.reverse_post_detail = reverse(
            'post:post_detail',
            kwargs={'post_id': cls.posts_data_list[0].id})
        cls.reverse_post_edit = reverse(
            'post:post_edit', kwargs={'post_id': cls.posts_data_list[0].id})
        cls.reverse_post_create = reverse('post:post_create')
        cls.small_gif = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.image_adress = 'posts/small.gif'
        cls.post_with_image = Post.objects.create(
            text='Test post with image.',
            group=cls.test_group,
            author=cls.user,
            image=cls.uploaded_image
        )
        cls.reverse_post_with_image_detail = reverse(
            'post:post_detail',
            kwargs={'post_id': cls.post_with_image.pk})
        cls.reverse_profile_follow = reverse(
            'post:profile_follow',
            kwargs={'username': cls.user}
        )
        cls.reverse_profile_unfollow = reverse(
            'post:profile_unfollow',
            kwargs={'username': cls.user2}
        )
        cls.follow_object = Follow.objects.create(
            user=cls.user,
            author=cls.user2
        )
        cls.follow_object2 = Follow.objects.create(
            user=cls.user3,
            author=cls.user
        )
        cls.reverse_profile2 = reverse(
            'post:profile',
            kwargs={'username': TaskPagesTests.user2.username})
        cls.reverse_follow_index = reverse('post:follow_index')
        cls.REVERSE_LIBRARY = {
            'index': cls.reverse_index,
            'group_list': cls.reverse_group_list,
            'group_list2': cls.reverse_group_list2,
            'profile': cls.reverse_profile,
            'profile2': cls.reverse_profile2,            
            'post_detail': cls.reverse_post_detail,
            'post_with_image_detail': cls.reverse_post_with_image_detail,
            'post_edit': cls.reverse_post_edit,
            'post_create': cls.reverse_post_create,
            'profile_follow': cls.reverse_profile_follow,
            'profile_unfollow': cls.reverse_profile_unfollow,
            'follow_index': cls.reverse_follow_index        
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.REVERSE_LIBRARY['index']: 'posts/index.html',
            self.REVERSE_LIBRARY['group_list']: 'posts/group_list.html',
            self.REVERSE_LIBRARY['profile']: 'posts/profile.html',
            self.REVERSE_LIBRARY['post_edit']: 'posts/create_post.html',
            self.REVERSE_LIBRARY['post_create']: 'posts/create_post.html', }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Context view-функции index работает правильно"""
        response_index = self.guest_client.get(self.REVERSE_LIBRARY['index'])
        posts = response_index.context['page_obj']
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_post.author)
                self.assertEqual(post.group, checked_post.group)
        self.assertEqual(
            len(response_index.context['page_obj']),
            PAGINATOR_CONSTANT)
        response_index_second_page = self.client.get(
            self.REVERSE_LIBRARY['index'] + '?page=2')
        self.assertEqual(
            len(response_index_second_page.context['page_obj']),
            Post.objects.all().count() - PAGINATOR_CONSTANT)

    def test_group_list_context(self):
        """Context view-функции group_list работает правильно"""
        response_group_list = self.guest_client.get(
            self.REVERSE_LIBRARY['group_list'])
        posts = response_group_list.context['page_obj']
        group = self.test_group
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)
        self.assertEqual(
            len(response_group_list.context['page_obj']), PAGINATOR_CONSTANT)
        response_group_list_second_page = self.client.get(
            self.REVERSE_LIBRARY['index'] + '?page=2')
        self.assertEqual(
            len(response_group_list_second_page.context['page_obj']),
            Post.objects.all().count() - PAGINATOR_CONSTANT)
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_post.author)
                self.assertEqual(post.group, group)

    def test_group_aya_list_context(self):
        """Проверяем, не попали ли посты из группы yay в группу aya"""
        response_group_list2 = self.guest_client.get(
            self.REVERSE_LIBRARY['group_list2'])
        posts = response_group_list2.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                self.assertNotIn(checked_post, posts)

    def test_profile_context(self):
        """Context view-функции profile работает правильно"""
        response_profile = self.guest_client.get(
            self.REVERSE_LIBRARY['profile'])
        posts = response_profile.context['page_obj']
        post_count = response_profile.context['post_count']
        self.assertIn(self.post_with_image, posts)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=self.post_with_image.pk).image)
        self.assertEqual(
            len(response_profile.context['page_obj']),
            PAGINATOR_CONSTANT)
        response_profile_second_page = self.client.get(
            self.REVERSE_LIBRARY['index'] + '?page=2')
        self.assertEqual(
            len(response_profile_second_page.context['page_obj']),
            Post.objects.all().count() - PAGINATOR_CONSTANT)
        for post in posts:
            with self.subTest(post=post):
                checked_post = Post.objects.get(id=post.id)
                checked_post_count = checked_post.author.posts.all().count()
                checked_author = self.user
                self.assertEqual(post.text, checked_post.text)
                self.assertEqual(post.author, checked_author)
                self.assertEqual(checked_post_count, post_count)

    def test_post_detail_context(self):
        response_post_detail = self.guest_client.get(
            self.REVERSE_LIBRARY['post_detail'])
        context_post = response_post_detail.context['post']
        context_post_count = response_post_detail.context['post_count']
        checked_post = Post.objects.get(id=context_post.id)
        checked_post_count = context_post.author.posts.all().count()
        self.assertEqual(context_post.text, checked_post.text)
        self.assertEqual(checked_post_count, context_post_count)

    def test_post_with_image_detail_context(self):
        response_post_detail = self.guest_client.get(
            self.REVERSE_LIBRARY['post_with_image_detail'])
        context_post = response_post_detail.context['post']
        checked_post = Post.objects.get(id=context_post.id)
        self.assertEqual(context_post.text, checked_post.text)
        self.assertEqual(
            self.post_with_image.image,
            Post.objects.get(pk=context_post.pk).image)


    def test_post_edit_context(self):
        response_post_edit = self.authorized_client.get(
            self.REVERSE_LIBRARY['post_edit'])
        context_author = response_post_edit.context['user']
        checked_author = Post.objects.get(id=self.posts_data_list[0].id).author
        self.assertEqual(context_author, checked_author)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_post_edit.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_context(self):
        response_post_edit = self.authorized_client.get(
            self.REVERSE_LIBRARY['post_create'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_post_edit.context.get(
                    'form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_template_cash(self):
        """Проверяем, кешируется ли главная страница"""
        deleted_post = Post.objects.get(pk=self.posts_data_list[14].id)
        content_index1 = self.guest_client.get(self.REVERSE_LIBRARY['index']).content
        deleted_post.delete()
        content_index2 = self.guest_client.get(self.REVERSE_LIBRARY['index']).content
        self.assertEqual(content_index1, content_index2)

    def test_profile_follow(self):
        response_profile_follow = self.authorized_client2.get(
            self.REVERSE_LIBRARY['profile_follow'])
        self.assertRedirects(
            response_profile_follow,
            self.REVERSE_LIBRARY['profile']
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user2, author=self.user).exists()
        )
        pass

    def test_profile_unfollow(self):
        response_profile_unfollow = self.authorized_client.get(
            self.REVERSE_LIBRARY['profile_unfollow'])
        self.assertRedirects(
            response_profile_unfollow,
            self.REVERSE_LIBRARY['profile2']
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user2).exists()
        )

    def test_follow_index(self):
        response_followed_index = self.authorized_client3.get(
            self.REVERSE_LIBRARY['follow_index'])
        page_obj_followed = response_followed_index.context['page_obj']
        self.assertIn(self.posts_data_list[12], page_obj_followed)
        response_not_followed_index = self.authorized_client.get(
            self.REVERSE_LIBRARY['follow_index'])
        page_obj_not_followed = response_not_followed_index.context['page_obj']
        self.assertNotIn(self.user3_post, page_obj_not_followed)

