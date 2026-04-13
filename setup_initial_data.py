"""
Wolecen EGL — Initial data setup script.
Run after migrations: python setup_initial_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wolecen_payment.settings')
django.setup()

from apps.accounts.models import User, Department
from apps.payments.models import PaymentCategory


def create_departments():
    departments = [
        ('TECH', 'Technical Operations'),
        ('FIN', 'Finance & Accounts'),
        ('HR', 'Human Resources'),
        ('OPS', 'Operations'),
        ('SALES', 'Sales & Business Development'),
        ('PROJ', 'Project Management'),
        ('ICT', 'ICT & Systems'),
        ('MGMT', 'Management'),
    ]
    created = 0
    for code, name in departments:
        dept, c = Department.objects.get_or_create(code=code, defaults={'name': name})
        if c:
            created += 1
            print(f'  ✓ Department: {dept}')
    print(f'  → {created} departments created.\n')


def create_categories():
    categories = [
        ('SUPPLIES', 'Office Supplies & Stationery', False, None),
        ('TRAVEL', 'Travel & Accommodation', True, None),
        ('UTILITIES', 'Utilities & Bills', False, None),
        ('EQUIPMENT', 'Equipment & Machinery', False, None),
        ('MAINT', 'Maintenance & Repairs', False, None),
        ('SERVICES', 'Professional Services', True, None),
        ('FUEL', 'Fuel & Transport', True, None),
        ('TRAINING', 'Training & Development', True, None),
        ('TELECOM', 'Telecom & Network Costs', False, None),
        ('OTHER', 'Other / Miscellaneous', False, None),
    ]
    created = 0
    for code, name, docs, max_amt in categories:
        cat, c = PaymentCategory.objects.get_or_create(
            code=code,
            defaults={'name': name, 'requires_additional_docs': docs, 'max_amount': max_amt}
        )
        if c:
            created += 1
            print(f'  ✓ Category: {cat.name}')
    print(f'  → {created} categories created.\n')


def create_superadmin():
    email = 'admin@wolecen.com'
    if User.objects.filter(email=email).exists():
        print(f'  → Admin user already exists: {email}\n')
        return

    admin = User.objects.create_superuser(
        username='admin',
        email=email,
        password='WolecenAdmin2024!',
        first_name='System',
        last_name='Administrator',
        role=User.Role.ADMIN,
    )
    print(f'  ✓ Superadmin created: {email}')
    print(f'  ✓ Password: WolecenAdmin2024! (CHANGE IMMEDIATELY)\n')


def create_demo_users():
    """Create demo users for testing all roles"""
    fin_dept, _ = Department.objects.get_or_create(code='FIN', defaults={'name': 'Finance & Accounts'})
    ops_dept, _ = Department.objects.get_or_create(code='OPS', defaults={'name': 'Operations'})

    users = [
        ('requester@wolecen.com', 'John', 'Mwamba', User.Role.REQUESTER, ops_dept, 'WEG-001'),
        ('supervisor@wolecen.com', 'Mary', 'Kimani', User.Role.REVIEWER1, ops_dept, 'WEG-002'),
        ('fincontroller@wolecen.com', 'Patrick', 'Oduya', User.Role.REVIEWER2, fin_dept, 'WEG-003'),
        ('finance@wolecen.com', 'Grace', 'Msela', User.Role.FINANCE, fin_dept, 'WEG-004'),
        ('auditor@wolecen.com', 'David', 'Ngowi', User.Role.AUDITOR, fin_dept, 'WEG-005'),
    ]

    created = 0
    for email, first, last, role, dept, emp_id in users:
        if not User.objects.filter(email=email).exists():
            u = User.objects.create_user(
                username=email,
                email=email,
                password='WolecenDemo2024!',
                first_name=first,
                last_name=last,
                role=role,
                department=dept,
                employee_id=emp_id,
            )
            created += 1
            print(f'  ✓ {role}: {u.full_name} ({email})')

    print(f'  → {created} demo users created (password: WolecenDemo2024!)\n')


if __name__ == '__main__':
    print('\n' + '═'*55)
    print('  WOLECEN EGL — Initial Data Setup')
    print('═'*55 + '\n')

    print('Creating departments...')
    create_departments()

    print('Creating payment categories...')
    create_categories()

    print('Creating superadmin...')
    create_superadmin()

    print('Creating demo users...')
    create_demo_users()

    print('═'*55)
    print('  Setup complete! Run: python manage.py runserver')
    print('═'*55 + '\n')
