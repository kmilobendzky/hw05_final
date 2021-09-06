from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName',)
        cls.test_post = Post.objects.create(text='Test post.',
                                            author=cls.user,)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.templates_url_names = {
            'posts/index.html': '/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
            'posts/profile.html': f'/profile/{cls.user.username}/',
        }
        cls.urls_status_codes = {
            '/': HTTPStatus.OK,
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
            f'/profile/{cls.user.username}/': HTTPStatus.OK,
            f'/posts/{cls.test_post.pk}/': HTTPStatus.OK
        }
        cls.response_adresses_library = {
            'test_post_edit_authorozed': (
                f'/posts/{cls.test_post.pk}/edit/'),
            'test_post_edit_unauthorozed': (
                f'/auth/login/?next=/posts/{cls.test_post.pk}/edit/'),
            'test_post_create': ('/create/'),
            'test_post_create_unauthorized': (
                '/auth/login/?next=/create/'),
            'unexisting_adress': ('/darkh01m/')
        }

    def setUp(self):
        cache.clear()

    def test_urls_correct_status_codes(self):
        """URL-адреса работают корректно"""
        for adress, code in self.urls_status_codes.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                cache.clear()
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_post_edit_correct_work(self):
        response_unauthorized = self.guest_client.get(
            self.response_adresses_library['test_post_edit_authorozed'],
            follow=True)
        self.assertRedirects(
            response_unauthorized,
            self.response_adresses_library['test_post_edit_unauthorozed']
        )
        response_authorized = self.authorized_client.get(
            self.response_adresses_library['test_post_edit_authorozed'])
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK)

    def test_post_create_correct_work(self):
        response_unauthorized = self.guest_client.get(
            self.response_adresses_library['test_post_create'],
            follow=True)
        self.assertRedirects(
            response_unauthorized,
            self.response_adresses_library['test_post_create_unauthorized']
        )
        response_authorized = self.authorized_client.get(
            self.response_adresses_library['test_post_create'])
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK)

    def error_404_check(self):
        response = self.guest_client.get(
            self.response_adresses_library['unexisting_adress'], follow=True)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
