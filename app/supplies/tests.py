from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Product
from users.tests import (
    PASSWORD,
    auth_client,
    create_company,
    create_storage,
    login,
)


class SuppliesApiTests(TestCase):
    def setUp(self):
        self.owner = auth_client()
        self.company = create_company(self.owner)
        self.storage = create_storage(self.owner)
        self.worker_user = get_user_model().objects.create_user(
            email='worker@email.com',
            password=PASSWORD,
            first_name='Валерий',
            last_name='Винтура',
        )
        attached = self.owner.post(
            f'/api/companies/{self.company["id"]}/members/',
            {'email': 'worker@email.com'},
            format='json',
        )
        self.assertEqual(attached.status_code, 201, attached.data)
        self.worker = login('worker@email.com')

    def test_supplier_product_and_invoice(self):
        supplier = self.worker.post(
            '/api/suppliers/',
            {'name': 'ООО Поставщик', 'inn': '880055535355'},
            format='json',
        )
        self.assertEqual(supplier.status_code, 201, supplier.data)
        self.assertEqual(supplier.data['company'], self.company['id'])

        listed = self.owner.get('/api/suppliers/')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)

        monitor = self.worker.post(
            '/api/products/',
            {
                'title': 'Монитор Asus',
                'description': '24 дюйма',
                'purchase_price': 1000,
                'sale_price': 1400,
            },
            format='json',
        )
        self.assertEqual(monitor.status_code, 201, monitor.data)
        self.assertEqual(monitor.data['quantity'], 0)
        self.assertEqual(monitor.data['storage'], self.storage['id'])

        case = self.owner.post(
            '/api/products/',
            {'title': 'Чехол для iPhone 15', 'purchase_price': 15, 'sale_price': 25},
            format='json',
        )
        self.assertEqual(case.status_code, 201, case.data)

        with_quantity = self.worker.post(
            '/api/products/',
            {
                'title': 'Клавиатура Razer',
                'quantity': 5,
                'purchase_price': 350,
                'sale_price': 680,
            },
            format='json',
        )
        self.assertEqual(with_quantity.status_code, 400)
        self.assertIn('quantity', with_quantity.data)

        supply = self.worker.post(
            '/api/supplies/',
            {
                'supplier_id': supplier.data['id'],
                'delivery_date': '2026-10-02',
                'products': [
                    {'id': monitor.data['id'], 'quantity': 10},
                    {'id': case.data['id'], 'quantity': 50},
                ],
            },
            format='json',
        )
        self.assertEqual(supply.status_code, 201, supply.data)
        self.assertEqual(supply.data['supplier_name'], 'ООО Поставщик')
        quantites = {item['title']: item['quantity'] for item in supply.data['products']}
        self.assertEqual(quantites, {'Монитор Asus': 10, 'Чехол для iPhone 15': 50})

        products = self.owner.get('/api/products/')
        self.assertEqual(products.status_code, 200)
        by_title = {item['title']: item['quantity'] for item in products.data}
        self.assertEqual(by_title['Монитор Asus'], 10)
        self.assertEqual(by_title['Чехол для iPhone 15'], 50)

        edited = self.worker.patch(
            f'/api/products/{monitor.data["id"]}/',
            {'sale_price': 1400, 'quantity': 1},
            format='json',
        )
        self.assertEqual(edited.status_code, 400)
        price_only = self.worker.patch(
            f'/api/products/{monitor.data["id"]}/',
            {'sale_price': 1400},
            format='json',
        )
        self.assertEqual(price_only.status_code, 200, price_only.data)
        self.assertEqual(price_only.data['quantity'], 10)
        self.assertEqual(price_only.data['sale_price'], 1400)

        supplies = self.owner.get('/api/supplies/')
        self.assertEqual(len(supplies.data), 1)

        invoice = self.owner.get(f'/api/supplies/{supply.data["id"]}/invoice/')
        self.assertEqual(invoice.status_code, 200, invoice.data)
        self.assertEqual(invoice.data['Поставщик'], 'ООО Поставщик')
        self.assertEqual(invoice.data['ИНН'], '880055535355')
        self.assertEqual(invoice.data['Товары']['Монитор Asus'], 10)
        self.assertEqual(invoice.data['Дата поставки'], '2026-10-02')
        self.assertEqual(invoice.data['Товары принял'], 'Тройнич Владислав')

        removed = self.owner.delete(f'/api/products/{monitor.data["id"]}/')
        self.assertEqual(removed.status_code, 400)
        removed_supplier = self.owner.delete(f'/api/suppliers/{supplier.data["id"]}/')
        self. assertEqual(removed_supplier.status_code, 400)

    def test_supply_accepts_product_list_and_rejects_bad_quantities(self):
        supplier = self.owner.post(
            '/api/suppliers/',
            {'name': 'ООО Опт', 'inn': '123456789012'},
            format='json',
        ).data
        product = self.owner.post(
            '/api/products/',
            {'title': 'Мышь', 'purchase_price': 300, 'sale_price': 500},
            format='json',
        ).data

        negative = self.owner.post(
            '/api/supplies/',
            {
                'supplier_id': supplier['id'],
                'delivery_date': '2026-10-03',
                'products': [
                    {'id': product['id'], 'quantity': 4},
                    {'id': product['id'], 'quantity': -1},
                ],
            },
            format='json',
        )
        self.assertEqual(negative.status_code, 400)
        self.assertEqual(Product.objects.get(pk=product['id']).quantity, 0)

        missing = self.owner.post(
            '/api/supplies/',
            {
                'supplier_id': supplier['id'],
                'delivery_date': '2026-10-03',
                'products': [
                    {'id': product['id'], 'quantity': 4},
                    {'id': 99999, 'quantity': -1},
                ],
            },
            format='json',
        )
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(Product.objects.get(pk=product['id']).quantity, 0)

        as_list = self.owner.post(
            f'/api/supplies/?supplier_id={supplier["id"]}&delivery_date=2026-10-03',
            [{'id': product['id'], 'quantity': 4}],
            format='json',
        )
        self.assertEqual(as_list.status_code, 201, as_list.data)
        self.assertEqual(Product.objects.get(pk=product['id']).quantity, 4)

        without_date = self.owner.post(
            '/api/supplies/',
            {
                'supplier_id': supplier['id'],
                'products': [{'id': product['id'], 'quantity': 2}],
            },
            format='json',
        )
        self.assertEqual(without_date.status_code, 201, without_date.data)
        self.assertIsNotNone(without_date.data['delivery_date'])
        self.assertEqual(Product.objects.get(pk=product['id']).quantity, 6)

    def test_access_and_membership_rules(self):
        outsider = auth_client('other@email.com', 'Олег', 'Смирнов')
        other_company = create_company(outsider, name='ООО Другая компания', inn='103876543210')
        create_storage(outsider)

        self.assertEqual(outsider.get('/api/suppliers/').status_code, 200)
        self.assertEqual(outsider.get('/api/suppliers/').data, [])
        self.assertEqual(outsider.post('/api/companies/1/members/', {'id': 1}, format='json').status_code, 403)

        free = auth_client('free@email.com', 'Рита', 'Магиладзе')
        self.assertEqual(free.get('/api/products/').status_code, 403)
        self.assertEqual(free.post('/api/suppliers/', {'name': 'Чужой', 'inn': '1234567890'}, format='json').status_code, 403)

        no_storage = auth_client('nostorage@email.com', 'Ирина', 'Орлова')
        bare_company = create_company(no_storage, name='ООО Без склада', inn='123456789011')
        denied = no_storage.post(
            '/api/products/',
            {'title': 'Товар', 'purchase_price': 1, 'sale_price': 2},
            format='json',
        )
        self.assertEqual(denied.status_code, 400)

        owner_of_other = get_user_model().objects.get(email='other@email.com')
        cannot_hire_owner = self.owner.post(
            f'/api/companies/{self.company["id"]}/members/',
            {'id': owner_of_other.id},
            format='json',
        )
        self.assertEqual(cannot_hire_owner.status_code, 400)

        again = self.owner.post(
            f'/api/companies/{self.company["id"]}/members/',
            {'email': 'worker@email.com'},
            format='json',
        )
        self.assertEqual(again.status_code, 400)

        members = self.owner.get(f'/api/companies/{self.company["id"]}/members/')
        self.assertEqual(members.status_code, 200)
        emails = {item['email'] for item in members.data}
        self.assertIn('owner@email.com', emails)
        self.assertIn('worker@email.com', emails)
        self.assertEqual(self.worker.get(f'/api/companies/{self.company["id"]}/members/').status_code, 403)

        self.assertNotEqual(other_company['id'], self.company['id'])
        self.assertNotEqual(bare_company['id'], self.company['id'])

    def test_admin_lists_new_models(self):
        admin_user = get_user_model().objects.create_superuser('admin@email.com', PASSWORD)
        client = APIClient()
        client.force_login(admin_user)
        for url in (
            '/admin/suppliers/supplier/',
            '/admin/products/product/',
            '/admin/supplies/supply/',
            '/admin/products/product/add/',
        ):
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)

        schema = APIClient().get('/api/schema/')
        self.assertEqual(schema.status_code, 200)
        content = schema.content.decode()
        self.assertIn('/api/suppliers/', content)
        self.assertIn('/api/products/', content)
        self.assertIn('/api/supplies/', content)
        self.assertIn('/invoice/', content)
