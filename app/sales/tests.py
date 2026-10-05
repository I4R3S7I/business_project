from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from products.models import Product
from users.tests import PASSWORD, auth_client, create_company, create_storage, login


class SalesApiTests(TestCase):
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

        supplier = self.worker.post(
            '/api/suppliers/',
            {'name': 'ООО Поставщик', 'inn': '880055535355'},
            format='json',
        )
        self.assertEqual(supplier.status_code, 201, supplier.data)

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
        self.monitor = monitor.data

        case = self.owner.post(
            '/api/products/',
            {'title': 'Чехол для iPhone 15', 'purchase_price': 15, 'sale_price': 25},
            format='json',
        )
        self.assertEqual(case.status_code, 201, case.data)
        self.case = case.data

        supply = self.worker.post(
            '/api/supplies/',
            {
                'supplier_id': supplier.data['id'],
                'delivery_date': '2026-10-02',
                'products': [
                    {'id': self.monitor['id'], 'quantity': 20},
                    {'id': self.case['id'], 'quantity': 50},
                ],
            },
            format='json',
        )
        self.assertEqual(supply.status_code, 201, supply.data)

    def test_create_list_update_delete_sale(self):
        sale = self.worker.post(
            '/api/sales/',
            {
                'buyer_name': 'Владислав Тройнич',
                'product_sales': [
                    {'product': self.monitor['id'], 'quantity': 8},
                    {'product': self.case['id'], 'quantity': 10},
                ],
            },
            format='json',
        )
        self.assertEqual(sale.status_code, 201, sale.data)
        self.assertEqual(sale.data['buyer_name'], 'Владислав Тройнич')
        self.assertEqual(sale.data['company'], self.company['id'])
        self.assertIsNotNone(sale.data['sale_date'])
        quantities = {
            item['product']: item['quantity'] for item in sale.data['product_sales']
        }
        self.assertEqual(quantities[self.monitor['id']], 8)
        self.assertEqual(quantities[self.case['id']], 10)
        self. assertEqual(Product.objects.get(pk=self.monitor['id']).quantity, 12)
        self.assertEqual(Product.objects.get(pk=self.case['id']).quantity, 40)

        listed = self.owner.get('/api/sales/')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data['count'], 1)
        self.assertEqual(len(listed.data['results']), 1)

        updated = self.owner.patch(
            f'/api/sales/{sale.data["id"]}/',
            {'buyer_name': 'Олег Смирнов', 'sale_date': '2026-10-05'},
            format='json',
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['buyer_name'], 'Олег Смирнов')
        self.assertEqual(updated.data['sale_date'], '2026-10-05')
        self.assertEqual(Product.objects.get(pk=self.monitor['id']).quantity, 12)

        forbidden = self.owner.patch(
            f'/api/sales/{sale.data["id"]}/',
            {
                'buyers_name': 'Олег Смирнов',
                'product_sales': [{'product': self.monitor['id'], 'quantity': 1}],
            },
            format='json',
        )
        self.assertEqual(forbidden.status_code, 400)
        self.assertIn('product_sales', forbidden.data)

        deleted = self.owner.delete(f'/api/sales/{sale.data["id"]}/')
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(Product.objects.get(pk=self.monitor['id']).quantity, 20)
        self.assertEqual(Product.objects.get(pk=self.case['id']).quantity, 50)

    def test_sale_rejects_insufficient_stock_and_filters_by_period(self):
        insufficient = self.owner.post(
            '/api/sales/',
            {
                'buyer_name': 'Покупатель',
                'product_sales': [
                    {'product': self.monitor['id'], 'quantity': 100},
                ],
            },
            format='json'
        )
        self.assertEqual(insufficient.status_code, 400)
        self.assertEqual(Product.objects.get(pk=self.monitor['id']).quantity, 20)

        first = self.owner.post(
            '/api/sales/',
            {
                'buyer_name': 'Первый',
                'sale_date': '2026-10-01',
                'product_sales': [{'product': self.monitor['id'], 'quantity': 2}],
            },
            format='json',
        )
        self.assertEqual(first.status_code, 201, first.data)

        second = self.owner.post(
            '/api/sales/',
            {
                'buyer_name': 'Второй',
                'sale_date': '2026-10-10',
                'product_sales': [{'product': self.case['id'], 'quantity': 3}],
            },
            format='json',
        )
        self.assertEqual(second.status_code, 201, second.data)

        period = self.owner.get('/api/sales/?date_from=2026-10-05&date_to=2026-10-15')
        self.assertEqual(period.status_code, 200)
        self.assertEqual(period.data['count'], 1)
        self.assertEqual(period.data['results'][0]['buyer_name'], 'Второй')

    def test_admin_and_schema_include_sales(self):
        admin_user = get_user_model().objects.create_superuser('admin@admin.com', PASSWORD)
        client = APIClient()
        client.force_login(admin_user)
        response = client.get('/admin/sales/sale/')
        self.assertEqual(response.status_code, 200)

        schema = APIClient().get('/api/schema/')
        self.assertEqual(schema.status_code, 200)
        content = schema.content.decode()
        self.assertIn('/api/sales/', content)