# deals/tests/tests_form.py
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.test_group = Group.objects.create(
            title='yay', slug='yay', description='yay')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.test_post = Post.objects.create(
            text='Test post 1.', author=cls.user, group=cls.test_group)
        cls.form_data1 = {
            'text': 'Test post 3.',
            'group': cls.test_group.pk,
        }
        cls.response_authorized_post_create = cls.authorized_client.post(
            reverse('post:post_create'),
            data=cls.form_data1,
            follow=True
        )
        cls.form_data2 = {
            'text': 'Test post 1 was edited.',
            'group': cls.test_group.pk,
        }
        cls.response_authorized_post_edit = cls.authorized_client.post(
            reverse('post:post_edit', kwargs={'post_id': cls.test_post.pk}),
            data=cls.form_data2,
            follow=True
        )
        cls.reverse_test_post_create_simple = reverse('post:post_create')
        cls.reverse_test_post_create = reverse(
            'post:profile', kwargs={'username': cls.user.username})
        cls.reverse_test_post_edit_simple = reverse(
            'post:post_edit', kwargs={'post_id': cls.test_post.pk})
        cls.reverse_test_post_edit = reverse(
            'post:post_detail', kwargs={'post_id': cls.test_post.pk})
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
        cls.form_data_image = {
            'text': 'Test post with image.',
            'group': cls.test_group.pk,
            'image': cls.uploaded_image,
        }
        cls.image_adress = 'posts/small.gif'
        cls.test_post_for_comment = Post.objects.create(
            text='Test post for comment.',
            author=cls.user,
            group=cls.test_group
        )
        cls.test_comment_data ={
            'text': 'Test comment',
        }
        cls.reverse_comment_create = reverse(
            'post:add_comment', kwargs={'post_id': cls.test_post_for_comment.pk})
        cls.reverse_test_post_for_comment_details = reverse(
            'post:post_detail', kwargs={'post_id': cls.test_post_for_comment.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_post_create(self):
        """Валидная форма Post создает запись в базе данных."""
        posts_count = Post.objects.count()
        response_authorized_post_create = self.authorized_client.post(
            self.reverse_test_post_create_simple,
            data=self.form_data1,
            follow=True
        )
        self.assertRedirects(
            response_authorized_post_create,
            self.reverse_test_post_create)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data1['text'],
                group=self.test_group,
                author=self.user).exists()
        )

    def test_post_edit(self):
        """Редактирование поста создает корректное изменение в базе данных"""
        response_authorized_post_edit = self.authorized_client.post(
            self.reverse_test_post_edit_simple,
            data=self.form_data2,
            follow=True
        )
        self.assertRedirects(
            response_authorized_post_edit,
            self.reverse_test_post_edit)
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data2['text'],
                group=self.test_group,
                author=self.user,).exists())

    def test_post_image_create(self):
        posts_count = Post.objects.count()
        response_post_image = self.authorized_client.post(
            self.reverse_test_post_create_simple,
            data=self.form_data_image,
            follow=True)
        self.assertRedirects(response_post_image,
        self.reverse_test_post_create)
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertTrue(Post.objects.filter(
                text=self.form_data_image['text'],
                group=self.test_group,
                image=self.image_adress).exists()
        )
    
    def test_post_comment_create(self):
        """Валидная форма Comment создает новый пост и он появляется в БД и на странице поста"""
        comments_count = Comment.objects.count()
        response_authorized_comment_add = self.authorized_client.post(
            self.reverse_comment_create,
            data=self.test_comment_data,
            follow=True
        )
        self.assertRedirects(response_authorized_comment_add,
        self.reverse_test_post_for_comment_details)
        test_comment = Comment.objects.get(
            text=self.test_comment_data['text']
        )
        self.assertTrue(Comment.objects.filter(
                text=test_comment.text).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count+1)
        response_for_post = self.authorized_client.get(
            self.reverse_test_post_for_comment_details
        )
        self.assertIn(test_comment, response_for_post.context['comments'])
        
