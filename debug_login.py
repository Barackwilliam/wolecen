"""
DEBUG SCRIPT — Wolecen Login Diagnosis
Run hii kwenye Django shell:
    python manage.py shell < debug_login.py

Itachunguza kila hatua ya authentication moja kwa moja.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wolecen_payment.settings')

print("\n" + "="*60)
print("  WOLECEN LOGIN DEBUG TOOL")
print("="*60)

# ── 1. Check AUTH_USER_MODEL
from django.conf import settings
print(f"\n[1] AUTH_USER_MODEL     : {settings.AUTH_USER_MODEL}")
print(f"[2] AUTHENTICATION_BACKENDS:")
for b in getattr(settings, 'AUTHENTICATION_BACKENDS', ['(not set — using default)']):
    print(f"      {b}")

# ── 2. Check User model
from django.contrib.auth import get_user_model
User = get_user_model()
print(f"\n[3] User model          : {User}")
print(f"[4] USERNAME_FIELD      : {User.USERNAME_FIELD}")

# ── 3. List all users
print(f"\n[5] All users in database:")
users = User.objects.all()
if not users.exists():
    print("      ⚠  NO USERS FOUND — run setup_initial_data.py first!")
else:
    for u in users:
        print(f"      id={str(u.pk)[:8]}... | email={u.email} | username={u.username} | active={u.is_active} | role={u.role}")

# ── 4. Try authenticate directly
TEST_EMAIL = input("\nEnter email to test (or press Enter to skip): ").strip()
if TEST_EMAIL:
    TEST_PASS = input("Enter password: ").strip()

    print(f"\n[6] Trying authenticate(username='{TEST_EMAIL}', password='***')")
    from django.contrib.auth import authenticate
    user = authenticate(request=None, username=TEST_EMAIL, password=TEST_PASS)
    if user:
        print(f"      ✓ SUCCESS — authenticated as: {user.get_full_name()} ({user.email})")
    else:
        print(f"      ✗ FAILED — authenticate() returned None")

        # Check if user exists at all
        print(f"\n[7] Checking if email exists in DB...")
        try:
            u = User.objects.get(email__iexact=TEST_EMAIL)
            print(f"      ✓ User found: {u.email} | is_active={u.is_active}")
            print(f"      Checking password directly...")
            if u.check_password(TEST_PASS):
                print(f"      ✓ Password is CORRECT")
                print(f"      ⚠  Problem is in authentication backend, not credentials!")
                print(f"      → Check AUTHENTICATION_BACKENDS in settings.py")
            else:
                print(f"      ✗ Password is WRONG")
                print(f"      → Reset password: python manage.py changepassword {u.email}")
        except User.DoesNotExist:
            print(f"      ✗ NO USER with email '{TEST_EMAIL}'")
            print(f"      → Create user or check email spelling")
        except Exception as e:
            print(f"      ✗ Error: {e}")

    # ── 5. Check EmailBackend directly
    print(f"\n[8] Testing EmailBackend directly...")
    try:
        from apps.accounts.backends import EmailBackend
        backend = EmailBackend()
        user2 = backend.authenticate(request=None, username=TEST_EMAIL, password=TEST_PASS)
        if user2:
            print(f"      ✓ EmailBackend works — returned: {user2.email}")
        else:
            print(f"      ✗ EmailBackend returned None")
    except ImportError as e:
        print(f"      ✗ Cannot import EmailBackend: {e}")
        print(f"      → backends.py file is missing or not saved correctly")

print("\n" + "="*60 + "\n")