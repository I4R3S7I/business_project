from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from users.tests import PASSWORD, auth_client, create_company


class StorageApiTests(TestCase):
    def setUp(self):
        self.owner = auth_client(email='owner@email.com', first_name='Владислав', last_name='Тройнич')
        self.company = create_company(self.owner)
        self.address = 'Солигорск, Улица Заслонова, д.17'

    def test_owner_manages_single_storage(self):
        created = self.owner.post(
            '/api/storages/',
            {'address': self.address, 'company': self.company['id']},
            format='json',
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data['address'], self.address)
        self.assertEqual(created.data['company'], self.company['id'])

        me = self.owner.get('/api/users/me/')
        self.assertEqual(me.data['storage_id'], created.data['id'])

        duplicate = self.owner.post(
            '/api/storages/',
            {'address': 'Другой адрес'},
            format='json',
        )
        self.assertEqual(duplicate.status_code, 400)

        updated = self.owner.patch(
            f'/api/storages/{created.data["id"]}/',
            {'address': 'Минск, улица Пушкина, д.11'},
            format='json',
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['address'], 'Минск, улица Пушкина, д.11')

        empty = self.owner.patch(
            f'/api/storages/{created.data["id"]}/',
            {'address': '   '},
            format='json',
        )
        self.assertEqual(empty.status_code, 400)

        deleted = self.owner.delete(f'/api/storages/{created.data["id"]}/')
        self.assertEqual(deleted.status_code, 204)
        recreated = self.owner.post(
            '/api/storages/',
            {'address': self.address},
            format='json',
        )
        self.assertEqual(recreated.status_code, 201)

    def test_member_can_read_but_cannot_change_storage(self):
        created = self.owner.post('/api/storages/', {'address': self.address}, format='json')
        User = get_user_model()
        User.objects.create_user(
            email='worker@email.com',
            password=PASSWORD,
            first_name='Павел',
            last_name='Орлов',
            company_id=self.company['id'],
        )
        worker = APIClient()
        token = worker.post(
            '/api/auth/token/',
            {'email': 'worker@email.com', 'password': PASSWORD},
            format='json',
        )
        worker.credentials(HTTP_AUTHORIZATION=f'Bearer {token.data["access"]}')

        readable = worker.get(f'/api/storages/{created.data["id"]}/')
        self.assertEqual(readable.status_code, 200)
        self.assertEqual(readable.data['address'], self.address)

        self.assertEqual(
            worker.patch(
                f'/api/storages/{created.data["id"]}/',
                {'address': 'Новый адрес'},
                format='json',
            ).status_code,
            403,
        )
        self.assertEqual(worker.delete(f'/api/storages/{created.data["id"]}/').status_code, 403)
        self.assertEqual(
            worker.post('/api/storages/', {'address': 'Склад сотрудника'}, format='json').status_code,
            403,
        )

        stranger = auth_client(email='stranger@email.com', first_name='Олег', last_name='Смирнов')
        self.assertEqual(stranger.get(f'/api/storages/{created.data["id"]}/').status_code, 403)
        anonymous = APIClient()
        self.assertEqual(anonymous.get(f'/api/storages/{created.data["id"]}/').status_code, 401)

    def test_user_without_company_cannot_create_storage(self):
        client = auth_client(email='free@email.com', first_name='Рита', last_name='Магиладзе')
        response = client.post('/api/storages/', {'address': self.address}, format='json')
        self.assertEqual(response.status_code, 403)