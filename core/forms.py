from django import forms
from .models import Product, Category, Supplier, Customer, Purchase, StoreSetting


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier','invoice_no','purchase_date','payment_status']
        widgets = {'purchase_date': forms.DateInput(attrs={'type':'date'})}
class StoreSettingForm(forms.ModelForm):
    class Meta:
        model = StoreSetting
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'receipt_header': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Welcome to our store'}),
            'receipt_footer': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Thank you! Visit again.'}),
        }
        labels = {
            'store_name': 'Store name',
            'phone': 'Phone / WhatsApp number',
            'invoice_prefix': 'Bill number prefix',
            'receipt_width_mm': 'Receipt paper width',
            'receipt_header': 'Extra lines on top of bill',
            'receipt_footer': 'Footer message on bill',
            'receipt_show_barcode': 'Show barcode on bill',
            'label_width_mm': 'Barcode label width (mm)',
            'label_height_mm': 'Barcode label height (mm)',
        }
