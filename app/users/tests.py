from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework.test import APIClient


PASSWORD = 'My_super_password123!'

def auth_client(email='owner@email.com', first_name='Владислав', last_name='Тройнич'):
    client = APIClient()
    response = client.post(
        '/api/auth/register/',
        {
            'email': email,
            'password': PASSWORD,
            'password_confirm': PASSWORD,
            'first_name': first_name,
            'last_name': last_name,
        },
        format='json',
    )
    assert response.status_code == 201, response.data
    token_response = client.post(
        '/api/auth/token/',
        {'email': email, 'password': PASSWORD},
        format='json',
    )
    assert token_response.status_code == 200, token_response.data
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_response.data["access"]}')
    return client


def create_company(client, name='ООО Строитель', inn='1234567890'):
    response = client.post(
        '/api/companies/',
        {'name': name, 'inn': inn, 'description': 'Ремонт под ключ'},
        format='json',
    )
    assert response.status_code == 201, response.data
    return response.data


class AuthApiTests(TestCase):
    def test_register_login_and_me(self):
        client = APIClient()
        response = client.post(
            '/api/auth/register/',
            {
                'email': 'Owner@email.com',
                'password': PASSWORD,
                'password_confirm': PASSWORD,
                'first_name': 'Владислав',
                'last_name': 'Тройнич',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['email'], 'owner@email.com')
        self.assertEqual(response.data['first_name'], 'Владислав')
        self.assertNotIn('password', response.data)

        login = client.post(
            '/api/auth/token/',
            {'email': 'OWNER@email.com', 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data)
        self.assertIn('refresh', login.data)

        refresh = client.post(
            '/api/auth/token/refresh/',
            {'refresh': login.data['refresh']},
            format='json',
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertIn('access', refresh.data)

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        me = client.get('/api/users/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['email'], 'owner@email.com')
        self.assertFalse(me.data['is_company_owner'])
        self.assertIsNone(me.data['company_id'])
        self.assertIsNone(me.data['storage_id'])


    def test_duplicate_email_and_password_mismatch(self):
        User = get_user_model()
        User.objects.create_user(
            email='owner@email.com',
            password=PASSWORD,
            first_name='Владислав',
            last_name='Тройнич'
            )
        
        client = APIClient()
        duplicate = client.post(
            '/api/auth/register/',
            {
                'email': 'owner@email.com',
                'password': PASSWORD,
                'password_confirm': PASSWORD,
                'first_name': 'Владислав',
                'last_name': 'Тройнич',
            },
            format='json',
        )
        self.assertEqual(duplicate.status_code, 400)

        missmatch = client.post(
            '/api/auth/register/',
            {
                'email': 'regular@email.com',
                'password': PASSWORD,
                'password_confirm': 'Another_super_password123!',
                'first_name': 'Владислав',
                'last_name': 'Тройнич',
            },
            format='json',
        )
        self.assertEqual(missmatch.status_code, 400)
        self.assertIn('password_confirm', missmatch.data)


    def test_wrong_password_and_anonyomous_me(self):
        User = get_user_model()
        User.objects.create_user(
            email='owner@email.com',
            password=PASSWORD,
            first_name='Владислав',
            last_name='Тройнич'
            )
        
        client = APIClient()
        login = client.post(
            '/api/auth/token/',
            {'email': 'owner@email.com', 'password': 'Wrong_password123!'},
            format='json',
        )
        self.assertEqual(login.status_code, 401)
        me = client.get('/api/users/me/')
        self.assertEqual(me.status_code, 401)


    def test_schema_is_public(self):
        client = APIClient()
        schema = client.get('/api/schema/')
        self.assertEqual(schema.status_code, 200)
        docs = client.get('/api/docs/')
        self.assertEqual(docs.status_code, 200)


class AdminTests(TestCase):
    def test_user_company_and_storage_are_in_admin(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(email='admin@admin.com', password=PASSWORD)
        client = Client()
        client.force_login(admin_user)

        for url in (
            '/admin/users/user/',
            '/admin/users/user/add/',
            '/admin/companies/company/',
            '/admin/storage/storage/',
        ):
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)

        created = client.post(
            '/admin/users/user/add/',
            {
                'email': 'staff@email.com',
                'first_name': 'Анастасия',
                'last_name': 'Бань',
                'password1': PASSWORD,
                'password2': PASSWORD,
            },
        )
        self.assertEqual(created.status_code, 302, created.content)
        user = User.objects.get(email='staff@email.com')
        change = client.get(f'/admin/users/user/{user.pk}/change/')
        self.assertEqual(change.status_code, 200)