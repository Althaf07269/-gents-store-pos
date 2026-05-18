"""Thermal receipt PDF (58mm / 80mm) and barcode helpers for TVS-style printers."""
import io
import base64
import urllib.parse
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from barcode import Code128
from barcode.writer import ImageWriter


def normalize_phone(phone):
    digits = ''.join(c for c in (phone or '') if c.isdigit())
    if len(digits) == 10:
        digits = '91' + digits
    return digits


def build_whatsapp_text(sale, store, pdf_url=''):
    cur = store.currency or '₹'
    lines = [
        f'*{store.store_name}*',
        f'Bill: {sale.bill_no}',
        f'Date: {sale.created_at.strftime("%d-%m-%Y %I:%M %p")}',
        '----------------',
    ]
    for it in sale.items.select_related('product'):
        lines.append(f'{it.product.name} x{it.quantity} = {cur}{it.total:.2f}')
    lines.append('----------------')
    lines.append(f'*TOTAL: {cur}{sale.total:.2f}*')
    lines.append(f'Payment: {sale.get_payment_method_display()}')
    if store.phone:
        lines.append(f'Contact: {store.phone}')
    if pdf_url:
        lines.append(f'PDF bill: {pdf_url}')
    footer = (store.receipt_footer or '').strip()
    if footer:
        lines.append(footer.split('\n')[0])
    return '\n'.join(lines)


def whatsapp_url(phone, text):
    q = urllib.parse.quote(text)
    if phone:
        return f'https://wa.me/{phone}?text={q}'
    return f'https://wa.me/?text={q}'


def barcode_png_bytes(code):
    buf = io.BytesIO()
    Code128(str(code), writer=ImageWriter()).write(buf, options={
        'module_width': 0.25,
        'module_height': 8,
        'write_text': False,
        'quiet_zone': 2,
    })
    buf.seek(0)
    return buf.read()


def barcode_data_uri(code):
    return 'data:image/png;base64,' + base64.b64encode(barcode_png_bytes(code)).decode()


def _draw_centered(c, text, y, width, font='Helvetica', size=9):
    c.setFont(font, size)
    c.drawCentredString(width / 2, y, text[:48])
    return y - (size + 4)


def _draw_line(c, y, width, thick=0.5):
    c.setLineWidth(thick)
    c.line(4 * mm, y, width - 4 * mm, y)
    return y - 6


def build_thermal_pdf(sale, store):
    width_mm = store.receipt_width_mm or 80
    width = width_mm * mm
    items = list(sale.items.select_related('product'))
    height_mm = 45 + len(items) * 7 + (25 if store.receipt_show_barcode else 0)
    height_mm += len((store.receipt_footer or '').split('\n')) * 5
    height = max(height_mm, 90) * mm

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    y = height - 8 * mm
    cur = store.currency or '₹'

    c.setFont('Helvetica-Bold', 11)
    y = _draw_centered(c, store.store_name, y, width, 'Helvetica-Bold', 11)
    if store.address:
        y = _draw_centered(c, store.address.replace('\n', ' ')[:60], y, width, 'Helvetica', 8)
    if store.phone:
        y = _draw_centered(c, f'Ph: {store.phone}', y, width, 'Helvetica', 8)
    if store.receipt_header:
        for line in store.receipt_header.split('\n'):
            if line.strip():
                y = _draw_centered(c, line.strip(), y, width, 'Helvetica', 8)

    y = _draw_line(c, y, width)
    y = _draw_centered(c, f'Bill: {sale.bill_no}', y, width, 'Helvetica-Bold', 9)
    y = _draw_centered(
        c,
        sale.created_at.strftime('%d-%m-%Y %I:%M %p'),
        y,
        width,
        'Helvetica',
        8,
    )
    if sale.customer:
        name = sale.customer.name or 'Customer'
        y = _draw_centered(c, name[:40], y, width, 'Helvetica', 8)
        if sale.customer.phone:
            y = _draw_centered(c, sale.customer.phone, y, width, 'Helvetica', 8)

    y = _draw_line(c, y, width)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(3 * mm, y, 'Item')
    c.drawRightString(width - 3 * mm, y, 'Amt')
    y -= 10
    c.setFont('Helvetica', 8)

    for it in items:
        name = it.product.name
        if len(name) > 22:
            name = name[:20] + '..'
        detail = f'{name} x{it.quantity}'
        c.drawString(3 * mm, y, detail)
        c.drawRightString(width - 3 * mm, y, f'{cur}{it.total:.2f}')
        y -= 10
        if it.product.size or it.product.barcode:
            sub = []
            if it.product.size:
                sub.append(it.product.size)
            if it.product.barcode:
                sub.append(it.product.barcode[:14])
            c.setFont('Helvetica', 7)
            c.drawString(5 * mm, y, ' '.join(sub)[:36])
            c.setFont('Helvetica', 8)
            y -= 9

    y = _draw_line(c, y, width)
    c.setFont('Helvetica', 8)
    c.drawString(3 * mm, y, 'Subtotal')
    c.drawRightString(width - 3 * mm, y, f'{cur}{sale.subtotal:.2f}')
    y -= 11
    if sale.discount and sale.discount > 0:
        c.drawString(3 * mm, y, 'Discount')
        c.drawRightString(width - 3 * mm, y, f'-{cur}{sale.discount:.2f}')
        y -= 11
    c.setFont('Helvetica-Bold', 10)
    c.drawString(3 * mm, y, 'TOTAL')
    c.drawRightString(width - 3 * mm, y, f'{cur}{sale.total:.2f}')
    y -= 12
    c.setFont('Helvetica', 8)
    c.drawString(3 * mm, y, f'Pay: {sale.get_payment_method_display()}')
    y -= 14

    y = _draw_line(c, y, width)
    if store.receipt_show_barcode:
        try:
            img = ImageReader(io.BytesIO(barcode_png_bytes(sale.bill_no)))
            bw, bh = 45 * mm, 12 * mm
            c.drawImage(img, (width - bw) / 2, y - bh, bw, bh, preserveAspectRatio=True)
            y -= bh + 4
        except Exception:
            pass

    footer = store.receipt_footer or 'Thank you! Visit again.'
    for line in footer.split('\n'):
        if line.strip():
            y = _draw_centered(c, line.strip(), y, width, 'Helvetica', 8)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
