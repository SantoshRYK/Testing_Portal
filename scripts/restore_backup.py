# scripts/restore_backup.py
"""
Restore Backup Script
Run this to restore data from a backup (SUPERUSER ONLY)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.backup_manager import backup_manager


def main():
    """Restore from backup"""
    print("🔄 Restore from Backup")
    print("=" * 50)
    print("⚠️  WARNING: This will replace current data!")
    print("=" * 50)
    
    # List available backups
    backups = backup_manager.list_backups()
    
    if not backups:
        print("❌ No backups found!")
        return 1
    
    print("\n📦 Available Backups:\n")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup['folder_name']}")
        print(f"   Type: {backup['type']}")
        print(f"   Created: {backup['timestamp']}")
        print(f"   By: {backup['created_by']}")
        print(f"   Files: {backup['file_count']}")
        print()
    
    # Get user choice
    try:
        choice = int(input("Select backup number to restore (0 to cancel): "))
        
        if choice == 0:
            print("Cancelled.")
            return 0
        
        if choice < 1 or choice > len(backups):
            print("❌ Invalid choice!")
            return 1
        
        selected_backup = backups[choice - 1]
        
        # Confirm
        confirm = input(f"\n⚠️  Restore '{selected_backup['folder_name']}'? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return 0
        
        # Restore
        print("\n🔄 Restoring backup...")
        success, message = backup_manager.restore_backup(
            selected_backup['folder_name'],
            restored_by="superuser"
        )
        
        print(message)
        
        if success:
            print("\n✅ Restore completed successfully!")
            print("⚠️  Please restart the application for changes to take effect.")
        else:
            print("\n❌ Restore failed!")
            return 1
    
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())