from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import *


class DeveloperOnlyUserAdmin(BaseUserAdmin):
    """Only superuser (developer) can manage login accounts."""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.unregister(User)
admin.site.register(User, DeveloperOnlyUserAdmin)


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Shop details', {
            'fields': ('store_name', 'logo', 'address', 'phone'),
        }),
        ('Bill numbering', {
            'fields': ('invoice_prefix', 'currency'),
        }),
        ('Thermal receipt design', {
            'fields': (
                'receipt_width_mm', 'receipt_header', 'receipt_footer', 'receipt_show_barcode',
            ),
        }),
        ('Barcode label size (mm)', {
            'fields': ('label_width_mm', 'label_height_mm'),
        }),
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'supplier', 'purchase_date', 'total_amount', 'payment_status')
    list_filter = ('supplier', 'payment_status', 'purchase_date')
    search_fields = ('invoice_no', 'supplier__name')
    inlines = [PurchaseItemInline]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'cost_price', 'total')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'total', 'payment_method', 'created_at', 'created_by')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('bill_no',)
    inlines = [SaleItemInline]


admin.site.register([Category, Supplier, Customer, Product, StockHistory])
