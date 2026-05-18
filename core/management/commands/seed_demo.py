from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Category, Product, Supplier, StoreSetting


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@see7.com', 'admin123')
        StoreSetting.objects.get_or_create(
            store_name='SEE7 CLOTHINGS',
            defaults={
                'address': 'Your Store Address',
                'phone': '9999999999',
                'invoice_prefix': 'S7',
            },
        )
        shirts, _ = Category.objects.get_or_create(name='Shirts')
        pants, _ = Category.objects.get_or_create(name='Pants')
        Supplier.objects.get_or_create(name='Default Supplier', defaults={'phone': '9999999999'})
        Product.objects.get_or_create(
            barcode='100001',
            defaults={
                'name': 'Formal Shirt', 'category': shirts, 'brand': 'SEE7',
                'size': 'M', 'color': 'Blue', 'purchase_price': 799,
                'selling_price': 799, 'stock_quantity': 25,
            },
        )
        Product.objects.get_or_create(
            barcode='100002',
            defaults={
                'name': 'Jeans Pant', 'category': pants, 'brand': 'SEE7',
                'size': '32', 'color': 'Black', 'purchase_price': 1199,
                'selling_price': 1199, 'stock_quantity': 18,
            },
        )
        self.stdout.write(self.style.SUCCESS('SEE7 CLOTHINGS demo ready. Developer admin: admin / admin123'))
