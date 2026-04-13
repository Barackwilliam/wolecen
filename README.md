# Wolecen Engineering Group Limited
## Payment Request & Retirement System

---

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Supabase PostgreSQL credentials

# 3. Run migrations
python manage.py makemigrations accounts payments approvals audit
python manage.py migrate

# 4. Load initial data (departments, categories, admin user)
python setup_initial_data.py

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Start server
python manage.py runserver
```

### Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| System Admin | admin@wolecen.com | WolecenAdmin2024! |
| Requester | requester@wolecen.com | WolecenDemo2024! |
| Supervisor (L1) | supervisor@wolecen.com | WolecenDemo2024! |
| Finance Controller (L2) | fincontroller@wolecen.com | WolecenDemo2024! |
| Finance Officer | finance@wolecen.com | WolecenDemo2024! |
| Auditor | auditor@wolecen.com | WolecenDemo2024! |

> **Change all passwords immediately after first login.**

---

### Payment Workflow

```
Requester → Submit → Reviewer 1 (Supervisor) → Reviewer 2 (Finance Controller)
         → Finance Officer (Process & Complete) → Requester (Retirement)
         → Auditor/Finance (Verify) → CLOSED
```

### Project Structure

```
wolecen/
├── wolecen_payment/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/             # Users, roles, authentication
│   ├── payments/             # Payment requests, documents
│   ├── approvals/            # Workflow engine & approval actions
│   └── audit/                # Audit trail & reports
├── templates/
│   ├── base/base.html        # Master template
│   ├── accounts/             # Login, profile, users
│   ├── payments/             # Request CRUD, list, print
│   ├── approvals/            # Queue views
│   └── audit/                # Logs & reports
├── static/                   # CSS, JS, images
├── requirements.txt
├── manage.py
├── setup_initial_data.py
└── .env.example
```

### Supabase Setup

1. Create a new project at supabase.com
2. Go to **Settings → Database**
3. Copy the connection string (Transaction pooler recommended)
4. Paste values into `.env`:
   ```
   DB_HOST=aws-0-xx-xxx.pooler.supabase.com
   DB_USER=postgres.your-project-ref
   DB_PASSWORD=your-password
   DB_NAME=postgres
   DB_PORT=5432
   ```

### cPanel Deployment

1. Upload all files to `public_html/wolecen/` or a subdomain
2. Create a Python app in cPanel (Python 3.10+)
3. Point WSGI file to `wolecen_payment/wsgi.py`
4. Set environment variables from `.env`
5. Run `pip install -r requirements.txt` in cPanel terminal
6. Run `python manage.py migrate` and `collectstatic`

---

*Wolecen Engineering Group Limited — Internal System*
