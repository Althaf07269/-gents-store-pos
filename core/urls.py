from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pos/', views.pos, name='pos'),
    path('api/product/', views.product_lookup, name='product_lookup'),
    path('sale/create/', views.create_sale, name='create_sale'),
    path( "purchases/<int:pk>/labels/", views.purchase_labels, name="purchase_labels",),
    path('invoice/<int:pk>/', views.invoice, name='invoice'),
    path('invoice/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoice/<int:pk>/print/', views.receipt_print, name='receipt_print'),
    path('invoice/<int:pk>/whatsapp/', views.invoice_whatsapp, name='invoice_whatsapp'),
    path('barcode/<int:pk>/', views.barcode_label, name='barcode_label'),
    path('stock/', views.stock, name='stock'),
    path('purchases/', views.purchase_report, name='purchase_report'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    path('purchases/<int:pk>/edit/', views.purchase_edit, name='purchase_edit'),
    path('purchases/create/', views.create_purchase, name='create_purchase'),
    path('purchases/<int:pk>/update/', views.update_purchase, name='update_purchase'),
    path('api/supplier/save/', views.supplier_save, name='supplier_save'),
    path('api/supplier/<int:pk>/', views.supplier_get, name='supplier_get'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('reports/', views.reports, name='reports'),
]
