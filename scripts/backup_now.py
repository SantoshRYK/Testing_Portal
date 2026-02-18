# scripts/backup_now.py
"""
Manual Backup Script
Run this to create an immediate backup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.backup_manager import backup_manager
from utils.auth import get_current_user


def main():
    """Create manual backup"""
    print("🔄 Creating manual backup...")
    print("-" * 50)
    
    # Get username (if running from app) or use 'manual'
    try:
        user = get_current_user()
    except:
        user = "manual_script"
    
    success, message = backup_manager.create_backup(
        backup_type="manual",
        created_by=user
    )
    
    print(message)
    
    if success:
        print("\n📊 Backup Statistics:")
        print(f"   Total backups: {len(backup_manager.list_backups())}")
        print(f"   Backup size: {backup_manager.get_backup_size()}")
        print("\n✅ Backup completed successfully!")
    else:
        print("\n❌ Backup failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())