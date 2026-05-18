# Gents Store POS - Python Django Web App

## Features included
- Dashboard with today sales, stock value, low stock alert
- Product add/edit/delete
- Inventory stock view and stock history
- Fast POS billing screen
- Barcode scan/search billing
- Auto stock reduction after sale
- Sales invoice print
- PDF invoice download
- WhatsApp bill link
- Barcode label print page
- Purchase, reports, customer, supplier models
- Django admin panel

## Login
After setup, run seed command. Default login:

Username: `admin`
Password: `admin123`

## Run in VS Code or PyCharm

### 1. Open folder
Open the `gents_store_pos` folder in VS Code or PyCharm.

### 2. Create/activate virtual environment
Windows PowerShell:
```bash
python -m venv venv
venv\Scripts\activate
```

Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. Create database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create demo admin and products
```bash
python manage.py seed_demo
```

### 6. Run server
```bash
python manage.py runserver
```

Open:
```text
http://127.0.0.1:8000/
```

Admin panel:
```text
http://127.0.0.1:8000/admin/
```

## Notes
- This is a strong starter project, not final production software.
- WhatsApp sending opens WhatsApp with bill text. Real automatic WhatsApp API needs Meta WhatsApp Business API.
- For thermal printer, use browser print or connect POS printer as system printer.
