# scripts/list_backups.py
"""
List All Backups Script
Shows all available backups and their details
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.backup_manager import backup_manager


def main():
    """List all backups"""
    print("📦 Available Backups")
    print("=" * 70)
    
    backups = backup_manager.list_backups()
    
    if not backups:
        print("❌ No backups found!")
        return 0
    
    print(f"\nTotal backups: {len(backups)}")
    print(f"Total size: {backup_manager.get_backup_size()}\n")
    
    for i, backup in enumerate(backups, 1):
        backup_size = backup_manager.get_backup_size(backup['folder_name'])
        
        print(f"{i}. {backup['folder_name']}")
        print(f"   📅 Created: {backup['timestamp']}")
        print(f"   👤 By: {backup['created_by']}")
        print(f"   🏷️  Type: {backup['type']}")
        print(f"   📁 Files: {backup['file_count']}")
        print(f"   💾 Size: {backup_size}")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())