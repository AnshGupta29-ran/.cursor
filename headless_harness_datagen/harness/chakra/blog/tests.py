from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Category, Post, Comment

class BlogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='A test category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            category=self.category,
            content='This is a test post content.',
            status='published'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test comment.',
            is_approved=True
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(str(self.category), 'Test Category')

    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.slug, 'test-post')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)
        self.assertEqual(self.post.status, 'published')
        self.assertEqual(str(self.post), 'Test Post')

    def test_comment_creation(self):
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'This is a test comment.')
        self.assertTrue(self.comment.is_approved)
        self.assertEqual(str(self.comment), f'Comment by {self.user.username} on {self.post.title}')

class BlogViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            category=self.category,
            content='This is a test post content.',
            status='published'
        )

    def test_home_page_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail_page_status_code(self):
        response = self.client.get(f'/post/{self.post.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_category_page_status_code(self):
        response = self.client.get(f'/category/{self.category.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_search_results_page_status_code(self):
        response = self.client.get('/search/?q=test')
        self.assertEqual(response.status_code, 200)

    def test_about_page_status_code(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_contact_page_status_code(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 200)

    def test_create_post_requires_login(self):
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_edit_post_requires_login(self):
        response = self.client.get(f'/edit/{self.post.slug}/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_delete_post_requires_login(self):
        response = self.client.get(f'/delete/{self.post.slug}/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

class BlogAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            category=self.category,
            content='This is a test post content.',
            status='published'
        )

    def test_post_list_api(self):
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail_api(self):
        response = self.client.get(f'/api/posts/{self.post.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_category_list_api(self):
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)

    def test_category_detail_api(self):
        response = self.client.get(f'/api/categories/{self.category.slug}/')
        self.assertEqual(response.status_code, 200)