# scripts/cleanup_old_backups.py
"""
Cleanup Old Backups Script
Removes old backups keeping only recent ones
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.backup_manager import backup_manager


def main():
    """Cleanup old backups"""
    print("🗑️  Cleanup Old Backups")
    print("=" * 50)
    
    backups = backup_manager.list_backups()
    retention = backup_manager.config["retention_count"]
    
    print(f"Current backups: {len(backups)}")
    print(f"Retention policy: Keep last {retention} backups")
    
    if len(backups) <= retention:
        print("\n✅ No cleanup needed. All backups within retention policy.")
        return 0
    
    print(f"\n⚠️  {len(backups) - retention} backup(s) will be removed.")
    confirm = input("Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return 0
    
    print("\n🔄 Cleaning up...")
    backup_manager.cleanup_old_backups()
    
    new_count = len(backup_manager.list_backups())
    print(f"\n✅ Cleanup complete!")
    print(f"   Remaining backups: {new_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())