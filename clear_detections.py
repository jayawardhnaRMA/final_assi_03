#!/usr/bin/env python3
"""
Clear or archive old detection files
"""
import os
import glob
import shutil
from datetime import datetime

def clear_detections(archive=True):
    """Clear detection files, optionally archiving them first"""
    
    # Find all detection JSON files
    detection_files = glob.glob('detections_*.json')
    
    if not detection_files:
        print("No detection files found.")
        return
    
    print(f"Found {len(detection_files)} detection file(s)")
    
    if archive:
        # Create archive directory with timestamp
        archive_dir = f"detections_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(archive_dir, exist_ok=True)
        print(f"\nArchiving to: {archive_dir}/")
        
        # Move files to archive
        for file in detection_files:
            dest = os.path.join(archive_dir, os.path.basename(file))
            shutil.move(file, dest)
            print(f"  Archived: {file}")
        
        print(f"\n✓ {len(detection_files)} file(s) archived to {archive_dir}/")
    else:
        # Delete files permanently
        for file in detection_files:
            os.remove(file)
            print(f"  Deleted: {file}")
        
        print(f"\n✓ {len(detection_files)} file(s) deleted")
    
    print("\nYou can now start fresh with new detections!")

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Detection Files Manager")
    print("=" * 60)
    
    # Check if --delete flag is provided
    if '--delete' in sys.argv:
        print("\n⚠️  WARNING: This will permanently delete all detection files!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            clear_detections(archive=False)
        else:
            print("Cancelled.")
    else:
        print("\nThis will archive old detection files to a backup folder.")
        print("(Use --delete flag to permanently delete instead)")
        response = input("\nProceed? (yes/no): ")
        if response.lower() == 'yes':
            clear_detections(archive=True)
        else:
            print("Cancelled.")
