from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Sum, F, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .models import *
from .forms import *
from . import receipt
from .decorators import admin_required


def get_store():
    return StoreSetting.objects.first() or StoreSetting.objects.create()


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


@login_required
def dashboard(request):
    today = timezone.localdate()
    sales_today = Sale.objects.filter(created_at__date=today).aggregate(s=Sum('total'))['s'] or 0
    total_stock_value = sum(p.stock_quantity * p.purchase_price for p in Product.objects.all())
    low_stock = Product.objects.filter(stock_quantity__lte=F('min_stock_alert'))[:10]
    recent_sales = Sale.objects.order_by('-created_at')[:8]
    purchase_month = Purchase.objects.filter(
        purchase_date__year=today.year, purchase_date__month=today.month
    ).aggregate(s=Sum('total_amount'))['s'] or 0
    return render(request, 'core/dashboard.html', locals())


@login_required
def pos(request):
    return render(request, 'core/pos.html', {'products': Product.objects.all()[:100]})


@login_required
def product_lookup(request):
    q = request.GET.get('q', '')
    products = Product.objects.filter(barcode__iexact=q)[:1] or Product.objects.filter(name__icontains=q)[:10]
    data = [{
        'id': p.id, 'name': p.name, 'price': float(p.selling_price),
        'purchase_price': float(p.purchase_price), 'stock': p.stock_quantity,
        'barcode': p.barcode, 'size': p.size, 'color': p.color,
    } for p in products]
    return JsonResponse({'products': data})


@login_required
def create_sale(request):
    if request.method != 'POST':
        return redirect('pos')
    data = json.loads(request.body)
    items = data.get('items', [])
    if not items:
        return JsonResponse({'ok': False, 'error': 'No items selected'}, status=400)
    customer = None
    if data.get('customer_phone') or data.get('customer_name'):
        customer, _ = Customer.objects.get_or_create(
            phone=data.get('customer_phone', ''),
            defaults={'name': data.get('customer_name', '')},
        )
    bill_no = f"{get_store().invoice_prefix}{timezone.now().strftime('%Y%m%d%H%M%S')}"
    sale = Sale.objects.create(
        bill_no=bill_no, customer=customer,
        discount=Decimal(str(data.get('discount', 0))),
        tax=Decimal(str(data.get('tax', 0))),
        payment_method=data.get('payment_method', 'cash'),
        created_by=request.user,
    )
    subtotal = Decimal('0')
    for item in items:
        p = Product.objects.get(id=item['id'])
        qty = int(item['qty'])
        if p.stock_quantity < qty:
            return JsonResponse({'ok': False, 'error': f'Low stock for {p.name}'}, status=400)
        line_total = p.selling_price * qty
        SaleItem.objects.create(
            sale=sale, product=p, quantity=qty, price=p.selling_price,
            cost_price=p.purchase_price, total=line_total,
        )
        p.stock_quantity -= qty
        p.save()
        StockHistory.objects.create(product=p, change_type='out', quantity=-qty, note=f'Sale {bill_no}')
        subtotal += line_total
    sale.subtotal = subtotal
    sale.total = subtotal - sale.discount + sale.tax
    sale.save()
    return JsonResponse({
        'ok': True,
        'invoice_url': reverse('invoice', args=[sale.id]),
        'print_url': reverse('receipt_print', args=[sale.id]),
    })


def _invoice_context(request, sale, store):
    phone_raw = sale.customer.phone if sale.customer else ''
    phone_digits = receipt.normalize_phone(phone_raw)
    pdf_url = request.build_absolute_uri(reverse('invoice_pdf', args=[sale.id]))
    wa_text = receipt.build_whatsapp_text(sale, store, pdf_url)
    return {
        'sale': sale, 'store': store, 'phone_digits': phone_digits,
        'phone_raw': phone_raw, 'pdf_url': pdf_url, 'whatsapp_text': wa_text,
        'whatsapp_url': receipt.whatsapp_url(phone_digits, wa_text),
        'whatsapp_url_any': receipt.whatsapp_url('', wa_text),
        'barcode_uri': receipt.barcode_data_uri(sale.bill_no),
    }


@login_required
def invoice_whatsapp(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    store = get_store()
    phone = request.GET.get('phone', '')
    if not phone and sale.customer:
        phone = sale.customer.phone or ''
    phone = receipt.normalize_phone(phone)
    pdf_url = request.build_absolute_uri(reverse('invoice_pdf', args=[sale.id]))
    text = receipt.build_whatsapp_text(sale, store, pdf_url)
    return redirect(receipt.whatsapp_url(phone, text))


@login_required
def invoice(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    store = get_store()
    ctx = _invoice_context(request, sale, store)
    if request.GET.get('print') == '1':
        return render(request, 'core/receipt_print.html', ctx)
    return render(request, 'core/invoice.html', ctx)


@login_required
def invoice_pdf(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    store = get_store()
    pdf = receipt.build_thermal_pdf(sale, store)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{sale.bill_no}.pdf"'
    return response


@login_required
def receipt_print(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    store = get_store()
    ctx = _invoice_context(request, sale, store)
    return render(request, 'core/receipt_print.html', ctx)


@admin_required
def barcode_label(request, pk):
    product = get_object_or_404(Product, pk=pk)
    store = get_store()
    return render(request, 'core/barcode.html', {
        'product': product, 'store': store,
        'barcode_uri': receipt.barcode_data_uri(product.barcode),
    })


@login_required
def stock(request):
    return render(request, 'core/stock.html', {
        'items': Product.objects.all(),
        'history': StockHistory.objects.order_by('-created_at')[:50],
    })


@admin_required
def purchase_add(request):
    return render(request, 'core/purchase_add.html', {
        'suppliers': Supplier.objects.order_by('name'),
        'categories': Category.objects.order_by('name'),
        'purchase': None,
    })


@admin_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related('supplier').prefetch_related('items__product'),
        pk=pk,
    )
    return render(request, 'core/purchase_add.html', {
        'suppliers': Supplier.objects.order_by('name'),
        'categories': Category.objects.order_by('name'),
        'purchase': purchase,
    })


def _resolve_supplier(data):
    sid = data.get('supplier_id')
    if sid:
        return Supplier.objects.filter(pk=sid).first()
    name = (data.get('supplier_name') or '').strip()
    if name:
        return Supplier.objects.get_or_create(name=name)[0]
    return None


def _revert_purchase_stock(purchase):
    for it in purchase.items.select_related('product'):
        p = it.product
        p.stock_quantity -= it.quantity
        p.save()
        StockHistory.objects.create(
            product=p, change_type='adjust', quantity=-it.quantity,
            note=f'Edit revert {purchase.invoice_no}',
        )
    purchase.items.all().delete()


def _apply_purchase_items(purchase, items, invoice_no):
    total = Decimal('0')
    for item in items:
        if item.get('is_new'):
            barcode = (item.get('barcode') or '').strip()
            if not barcode:
                raise ValueError('Barcode required for new product')
            if Product.objects.filter(barcode=barcode).exists():
                raise ValueError(f'Barcode {barcode} already exists')
            cat = Category.objects.filter(pk=item['category_id']).first() if item.get('category_id') else None
            qty = int(item['qty'])
            purchase_rate = Decimal(str(item.get('price', 0)))
            selling_rate = Decimal(str(item.get('selling_price', 0)))
            if purchase_rate <= 0:
                raise ValueError('Purchase rate required for new product')
            if selling_rate <= 0:
                raise ValueError('Sales rate required for new product')
            p = Product.objects.create(
                name=item.get('name', 'Product'),
                category=cat,
                brand=item.get('brand', ''),
                size=item.get('size', ''),
                color=item.get('color', ''),
                purchase_price=purchase_rate,
                selling_price=selling_rate,
                barcode=barcode,
                stock_quantity=0,
                min_stock_alert=int(item.get('min_stock_alert', 5)),
            )
        else:
            p = Product.objects.get(id=item['id'])
            qty = int(item['qty'])
            purchase_rate = Decimal(str(item.get('price', 0)))
            selling_rate = Decimal(str(item.get('selling_price', p.selling_price)))
            if purchase_rate <= 0:
                raise ValueError(f'Purchase rate required for {p.name}')
            if selling_rate <= 0:
                raise ValueError(f'Sales rate required for {p.name}')

        PurchaseItem.objects.create(purchase=purchase, product=p, quantity=qty, price=purchase_rate)
        p.stock_quantity += qty
        p.purchase_price = purchase_rate
        p.selling_price = selling_rate
        p.save()
        StockHistory.objects.create(
            product=p, change_type='in', quantity=qty,
            note=f'Purchase {invoice_no}',
        )
        total += purchase_rate * qty
    return total


@admin_required
def create_purchase(request):
    if request.method != 'POST':
        return redirect('purchase_add')
    data = json.loads(request.body)
    items = data.get('items', [])
    if not items:
        return JsonResponse({'ok': False, 'error': 'Add at least one product'}, status=400)
    invoice_no = (data.get('invoice_no') or '').strip()
    if not invoice_no:
        return JsonResponse({'ok': False, 'error': 'Invoice number is required'}, status=400)
    if Purchase.objects.filter(invoice_no=invoice_no).exists():
        return JsonResponse({'ok': False, 'error': 'Invoice number already exists'}, status=400)

    purchase = Purchase.objects.create(
        supplier=_resolve_supplier(data),
        invoice_no=invoice_no,
        purchase_date=data.get('purchase_date') or timezone.localdate().isoformat(),
        payment_status=data.get('payment_status', 'paid'),
        created_by=request.user,
    )
    try:
        purchase.total_amount = _apply_purchase_items(purchase, items, invoice_no)
        purchase.save()
    except ValueError as e:
        purchase.delete()
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'url': reverse('purchase_detail', args=[purchase.id])})


@admin_required
def update_purchase(request, pk):
    if request.method != 'POST':
        return redirect('purchase_edit', pk=pk)
    purchase = get_object_or_404(Purchase, pk=pk)
    data = json.loads(request.body)
    items = data.get('items', [])
    if not items:
        return JsonResponse({'ok': False, 'error': 'Add at least one product'}, status=400)
    invoice_no = (data.get('invoice_no') or '').strip()
    if not invoice_no:
        return JsonResponse({'ok': False, 'error': 'Invoice number is required'}, status=400)
    if Purchase.objects.filter(invoice_no=invoice_no).exclude(pk=pk).exists():
        return JsonResponse({'ok': False, 'error': 'Invoice number already exists'}, status=400)

    _revert_purchase_stock(purchase)
    purchase.supplier = _resolve_supplier(data)
    purchase.invoice_no = invoice_no
    purchase.purchase_date = data.get('purchase_date') or purchase.purchase_date
    purchase.payment_status = data.get('payment_status', purchase.payment_status)
    try:
        purchase.total_amount = _apply_purchase_items(purchase, items, invoice_no)
        purchase.save()
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'url': reverse('purchase_detail', args=[purchase.id])})


@admin_required
def supplier_save(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    data = json.loads(request.body)
    sid = data.get('id')
    name = (data.get('name') or '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Supplier name required'}, status=400)
    if sid:
        supplier = get_object_or_404(Supplier, pk=sid)
        supplier.name = name
        supplier.phone = data.get('phone', '')
        supplier.address = data.get('address', '')
        supplier.save()
    else:
        supplier, _ = Supplier.objects.get_or_create(
            name=name,
            defaults={'phone': data.get('phone', ''), 'address': data.get('address', '')},
        )
    return JsonResponse({'ok': True, 'supplier': {
        'id': supplier.id, 'name': supplier.name,
        'phone': supplier.phone, 'address': supplier.address,
    }})


@admin_required
def supplier_get(request, pk):
    s = get_object_or_404(Supplier, pk=pk)
    return JsonResponse({'ok': True, 'supplier': {
        'id': s.id, 'name': s.name, 'phone': s.phone, 'address': s.address,
    }})


@admin_required
def purchase_report(request):
    qs = Purchase.objects.select_related('supplier').order_by('-purchase_date', '-id')
    supplier_id = request.GET.get('supplier', '')
    invoice_q = request.GET.get('invoice', '').strip()
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    if invoice_q:
        qs = qs.filter(invoice_no__icontains=invoice_q)
    if date_from:
        qs = qs.filter(purchase_date__gte=date_from)
    if date_to:
        qs = qs.filter(purchase_date__lte=date_to)

    summary = qs.aggregate(total=Sum('total_amount'), count=Count('id'))
    suppliers = Supplier.objects.order_by('name')
    return render(request, 'core/purchase_report.html', {
        'items': qs[:200],
        'suppliers': suppliers,
        'supplier_id': supplier_id,
        'invoice_q': invoice_q,
        'date_from': date_from,
        'date_to': date_to,
        'summary_total': summary['total'] or 0,
        'summary_count': summary['count'] or 0,
    })


@admin_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase.objects.select_related('supplier'), pk=pk)
    return render(request, 'core/purchase_detail.html', {'purchase': purchase})


def _report_date_range(period, date_str, month_str, year_str):
    today = timezone.localdate()
    if period == 'daily':
        d = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
        return d, d
    if period == 'monthly':
        if month_str:
            y, m = map(int, month_str.split('-'))
        else:
            y, m = today.year, today.month
        start = today.replace(year=y, month=m, day=1)
        if m == 12:
            end = start.replace(year=y + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=m + 1, day=1) - timedelta(days=1)
        return start, end
    # annual
    y = int(year_str) if year_str else today.year
    return today.replace(year=y, month=1, day=1), today.replace(year=y, month=12, day=31)


@login_required
def reports(request):
    period = request.GET.get('period', 'daily')
    date_str = request.GET.get('date', '')
    month_str = request.GET.get('month', '')
    year_str = request.GET.get('year', '')

    start, end = _report_date_range(period, date_str, month_str, year_str)
    sales_qs = Sale.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end,
    ).prefetch_related('items__product').order_by('-created_at')

    total_sales = Decimal('0')
    total_cost = Decimal('0')
    total_discount = Decimal('0')
    total_tax = Decimal('0')
    bill_rows = []
    payment_breakdown = {}
    product_sales = {}

    for sale in sales_qs:
        sale_cost = Decimal('0')
        sale_profit = Decimal('0')
        for it in sale.items.all():
            cost = it.cost_price * it.quantity
            sale_cost += cost
            sale_profit += it.total - cost
            key = it.product.name
            if key not in product_sales:
                product_sales[key] = {'qty': 0, 'amount': Decimal('0')}
            product_sales[key]['qty'] += it.quantity
            product_sales[key]['amount'] += it.total

        total_sales += sale.total
        total_cost += sale_cost
        total_discount += sale.discount
        total_tax += sale.tax
        payment_breakdown[sale.payment_method] = payment_breakdown.get(sale.payment_method, Decimal('0')) + sale.total
        bill_rows.append({
            'sale': sale,
            'cost': sale_cost,
            'profit': sale_profit,
        })

    total_profit = total_sales - total_cost - total_discount + total_tax
    # profit on items before discount/tax adjustment
    item_profit = sum(r['profit'] for r in bill_rows)
    purchase_total = Purchase.objects.filter(
        purchase_date__gte=start, purchase_date__lte=end,
    ).aggregate(s=Sum('total_amount'))['s'] or 0

    top_products = sorted(product_sales.items(), key=lambda x: x[1]['amount'], reverse=True)[:10]

    return render(request, 'core/reports.html', {
        'period': period,
        'date_str': date_str or start.isoformat(),
        'month_str': month_str or start.strftime('%Y-%m'),
        'year_str': year_str or str(start.year),
        'start': start, 'end': end,
        'total_sales': total_sales,
        'total_cost': total_cost,
        'total_profit': item_profit,
        'total_discount': total_discount,
        'total_tax': total_tax,
        'bill_count': len(bill_rows),
        'avg_bill': total_sales / len(bill_rows) if bill_rows else 0,
        'purchase_total': purchase_total,
        'bill_rows': bill_rows,
        'payment_breakdown': payment_breakdown,
        'top_products': top_products,
    })
