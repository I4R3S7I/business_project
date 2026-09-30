from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from companies.models import Company
from storage.models import Storage
from users.tests import PASSWORD, auth_client, create_company


class CompanyApiTests(TestCase):
    def test_owner_creates_updates_and_deletes_company(self):
        client = auth_client()
        created = create_company(client)
        self.assertEqual(created['name'], 'ООО Строитель')
        self.assertEqual(created['inn'], '1234567890')
        self.assertEqual(created['owner_email'], 'owner@email.com')

        User = get_user_model()
        owner = User.objects.get(email='owner@email.com')
        self.assertTrue(owner.is_company_owner)
        self.assertEqual(owner.company_id, created['id'])

        me = client.get('/api/users/me')
        self.assertEqual(me.data['company_id'], created['id'])
        self.assertTrue(me.data['is_company_owner'])

        anonymous = APIClient()
        hidden = anonymous.get(f'/api/companies/{created['id']}/')
        self.assertEqual(hidden.status_code, 401)

        stranger = auth_client('stranger@email.com, "Олег", "Смирнов"')
        visible = stranger.get(f'/api/companies/{created['id']}/')
        self.assertEqual(visible.status_code, 200)
        forbidden = stranger.patch(
            f'/api/companies/{created['id']}/',
            {'name': 'Чужая'},
            format='json',
        )
        self.assertEqual(forbidden.status_code, 403)

        updated = client.patch(
            f'/api/companies/{created['id']}/',
            {'name': 'ООО Строитель Люкс', 'description': 'Новое описание компании'},
            format='json',
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data['name'], 'ООО Строитель Люкс')

        second = client.post(
            '/api/companies/',
            {'name': 'Вторая', 'inn': '123456789876'},
            format='json',
        )
        self.assertEqual(second.status_code, 400)

        employee_attempt = stranger.post(
            '/api/companies/',
            {'name': 'Компания сотрудника', 'inn': '0987654321'},
            format='json',
        )
        self.assertEqual(employee_attempt.status_code, 201)
        User.objects.filter(email='stranger@email.com').update(
            company_id=created['id'],
            is_company_owner=False,
        )
        Company.objects.filter(pk=employee_attempt.data['id']).delete()
        blocked = stranger.post(
            '/api/companies/',
            {'name': 'Еще одна', 'inn': '0987654322'},
            format='json',
        )
        self.assertEqual(blocked.status_code, 400)

        deleted = client.delete(f'/api/companies/{created['id']}/')
        self.assertEqual(deleted.status_code, 204)
        owner.refresh_from_db()
        self.assertFalse(owner.is_company_owner)
        self.assertIsNone(owner.company_id)
        self.assertFalse(Company.objects.filter(pk=created['id']).exists())


    def test_invalid_inn_and_duplicate_name(self):
        client = auth_client()
        invalid = client.post(
            '/api/companies/',
            {'name': 'ООО СтройСам', 'inn': '12345'},
            format='json',
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertIn('inn', invalid.data)

        create_company(client)
        other = auth_client('second@email.com', 'Ирина', 'Орлова')
        duplicate = other.post(
            '/api/companies',
            {'name': 'ООО Строитель', 'inn': '123456789876'},
            format='json',
        )
        self.assertEqual(duplicate.status_code, 400)


    def test_delete_company_removes_storage_and_keeps_owner_consistent(self):
        client = auth_client()
        company = create_company(client)
        storage = client.post(
            '/api/storages/',
            {'address': 'Солигорск, Улица Заслонова, д.17'},
            format='json',
        )
        self.assertEqual(storage.status_code, 201)
        client.delete(f'/api/companies/{company['id']}/')
        self.assertFalse(Storage.objects.filter(pk=storage.data['id']).exists())