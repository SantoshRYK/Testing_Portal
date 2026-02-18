"""
Fix users.json - Add missing fields for compatibility
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
USERS_FILE = DATA_DIR / 'users.json'

# Load current users
with USERS_FILE.open('r', encoding='utf-8') as f:
    users = json.load(f)

# Fix each user
for username, user_data in users.items():
    # Add is_active if missing (default True)
    if 'is_active' not in user_data:
        user_data['is_active'] = True
        print(f"✅ Added is_active=True for {username}")
    
    # Add is_audit_reviewer if missing (default based on role)
    if 'is_audit_reviewer' not in user_data:
        # Superusers get audit reviewer by default
        if user_data.get('role') == 'superuser':
            user_data['is_audit_reviewer'] = True
        else:
            user_data['is_audit_reviewer'] = False
        print(f"✅ Added is_audit_reviewer={user_data['is_audit_reviewer']} for {username}")

# Save updated users
with USERS_FILE.open('w', encoding='utf-8') as f:
    json.dump(users, f, indent=4, ensure_ascii=False)

print("\n✅ Users file fixed!")
print("\nCurrent users:")
for username, data in users.items():
    print(f"  - {username}: {data.get('role')} (active: {data.get('is_active')}, audit: {data.get('is_audit_reviewer')})")