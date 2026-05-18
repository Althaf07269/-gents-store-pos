from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class StoreSetting(models.Model):
    RECEIPT_WIDTHS = [(58, '58 mm (2 inch)'), (80, '80 mm (3 inch / TVS)')]
    store_name = models.CharField(max_length=150, default='SEE7 CLOTHINGS')
    logo = models.ImageField(upload_to='store/', blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=50, blank=True)
    invoice_prefix = models.CharField(max_length=10, default='S7')
    currency = models.CharField(max_length=5, default='₹')
    receipt_width_mm = models.PositiveSmallIntegerField(choices=RECEIPT_WIDTHS, default=80)
    receipt_header = models.TextField(blank=True, help_text='Extra lines on bill (one per line)')
    receipt_footer = models.TextField(default='Thank you! Visit again.', blank=True)
    receipt_show_barcode = models.BooleanField(default=True, help_text='Print bill barcode on receipt')
    label_width_mm = models.PositiveSmallIntegerField(default=50)
    label_height_mm = models.PositiveSmallIntegerField(default=30)
    def __str__(self): return self.store_name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    def __str__(self): return self.name

class Customer(models.Model):
    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    def __str__(self): return self.name or self.phone or 'Walk-in Customer'

class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='GST % on this product')
    barcode = models.CharField(max_length=100, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_alert = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.name} - {self.barcode}'
    @property
    def is_low_stock(self): return self.stock_quantity <= self.min_stock_alert

class Purchase(models.Model):
    PAYMENT_STATUS = [('paid','Paid'),('pending','Pending'),('partial','Partial')]
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    invoice_no = models.CharField(max_length=100)
    purchase_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='paid')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self): return self.invoice_no

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.price * self.quantity

class Sale(models.Model):
    PAYMENT_METHODS = [('cash','Cash'),('upi','UPI'),('card','Card'),('mixed','Mixed')]
    bill_no = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.bill_no

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def profit(self):
        return self.total - (self.cost_price * self.quantity)

class StockHistory(models.Model):
    TYPES = [('in','Stock In'),('out','Stock Out'),('adjust','Adjustment'),('damage','Damaged'),('return','Return')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=20, choices=TYPES)
    quantity = models.IntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
