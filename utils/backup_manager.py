# utils/backup_manager.py
"""
Automatic Backup System
Handles automatic weekly backups and manual backups
"""
import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from config import (
    BASE_DIR, DATA_DIR, BACKUP_DIR, BACKUP_CONFIG,
    BACKUP_DATE_FORMAT, BACKUP_INFO_FILE
)


class BackupManager:
    """Manages automatic and manual backups"""
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.data_dir = DATA_DIR
        self.config = BACKUP_CONFIG
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_type: str = "manual", created_by: str = "system") -> tuple[bool, str]:
        """
        Create a new backup
        
        Args:
            backup_type: "manual", "automatic", "pre-write"
            created_by: Username who initiated backup
        
        Returns:
            (success, message)
        """
        try:
            # Create backup folder with timestamp
            timestamp = datetime.now().strftime(BACKUP_DATE_FORMAT)
            backup_name = f"{timestamp}_{backup_type}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy all data files
            files_backed_up = []
            for filename in self.config["include_files"]:
                source = os.path.join(self.data_dir, filename)
                destination = os.path.join(backup_path, filename)
                
                if os.path.exists(source):
                    shutil.copy2(source, destination)
                    files_backed_up.append(filename)
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "type": backup_type,
                "created_by": created_by,
                "files": files_backed_up,
                "file_count": len(files_backed_up),
                "backup_path": backup_path
            }
            
            info_path = os.path.join(backup_path, BACKUP_INFO_FILE)
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=4)
            
            # Auto cleanup if enabled
            if self.config["auto_cleanup"]:
                self.cleanup_old_backups()
            
            return True, f"✅ Backup created: {backup_name}"
        
        except Exception as e:
            return False, f"❌ Backup failed: {str(e)}"
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        try:
            for backup_folder in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_folder)
                
                if os.path.isdir(backup_path):
                    info_file = os.path.join(backup_path, BACKUP_INFO_FILE)
                    
                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            backup_info = json.load(f)
                            backup_info['folder_name'] = backup_folder
                            backups.append(backup_info)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups
        
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def restore_backup(self, backup_folder: str, restored_by: str = "superuser") -> tuple[bool, str]:
        """
        Restore data from a backup
        
        Args:
            backup_folder: Name of backup folder to restore
            restored_by: Username who initiated restore
        
        Returns:
            (success, message)
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_folder)
            
            if not os.path.exists(backup_path):
                return False, f"❌ Backup not found: {backup_folder}"
            
            # Create a safety backup before restore
            self.create_backup("pre-restore", restored_by)
            
            # Restore files
            restored_files = []
            for filename in os.listdir(backup_path):
                if filename == BACKUP_INFO_FILE:
                    continue
                
                source = os.path.join(backup_path, filename)
                destination = os.path.join(self.data_dir, filename)
                
                shutil.copy2(source, destination)
                restored_files.append(filename)
            
            # Log restore action
            restore_log = {
                "timestamp": datetime.now().strftime(BACKUP_DATE_FORMAT),
                "backup_restored": backup_folder,
                "restored_by": restored_by,
                "files_restored": restored_files
            }
            
            log_file = os.path.join(self.backup_dir, "restore_log.json")
            
            # Append to restore log
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(restore_log)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4)
            
            return True, f"✅ Restored {len(restored_files)} files from backup: {backup_folder}"
        
        except Exception as e:
            return False, f"❌ Restore failed: {str(e)}"
    
    def cleanup_old_backups(self):
        """Remove old backups, keeping only the last N backups"""
        try:
            backups = self.list_backups()
            retention_count = self.config["retention_count"]
            
            if len(backups) > retention_count:
                # Remove oldest backups
                backups_to_delete = backups[retention_count:]
                
                for backup in backups_to_delete:
                    # Skip manual and pre-restore backups
                    if backup['type'] in ['manual', 'pre-restore']:
                        continue
                    
                    backup_path = os.path.join(self.backup_dir, backup['folder_name'])
                    shutil.rmtree(backup_path)
                    print(f"🗑️ Removed old backup: {backup['folder_name']}")
        
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def get_backup_size(self, backup_folder: str = None) -> str:
        """Get size of backup folder(s)"""
        try:
            if backup_folder:
                path = os.path.join(self.backup_dir, backup_folder)
            else:
                path = self.backup_dir
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            
            # Convert to readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.2f} {unit}"
                total_size /= 1024.0
            
            return f"{total_size:.2f} TB"
        
        except Exception as e:
            return "Unknown"
    
    def should_create_automatic_backup(self) -> bool:
        """Check if automatic backup should be created now"""
        if not self.config["enabled"]:
            return False
        
        backups = self.list_backups()
        
        # Get last automatic backup
        last_auto_backup = None
        for backup in backups:
            if backup['type'] == 'automatic':
                last_auto_backup = backup
                break
        
        if last_auto_backup is None:
            return True  # No automatic backup exists
        
        # Parse last backup timestamp
        try:
            last_backup_time = datetime.strptime(
                last_auto_backup['timestamp'],
                BACKUP_DATE_FORMAT
            )
        except:
            return True
        
        # Check if enough time has passed
        now = datetime.now()
        
        if self.config["frequency"] == "daily":
            return (now - last_backup_time).days >= 1
        
        elif self.config["frequency"] == "weekly":
            # Check if it's the right day of week and 7 days passed
            current_day = now.weekday()
            target_day = self.config["day_of_week"]
            
            return (
                current_day == target_day and
                (now - last_backup_time).days >= 7
            )
        
        elif self.config["frequency"] == "monthly":
            return (now - last_backup_time).days >= 30
        
        return False


# Global backup manager instance
backup_manager = BackupManager()