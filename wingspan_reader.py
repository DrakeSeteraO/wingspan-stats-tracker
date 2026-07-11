import os
import sqlite3
import shutil
from pathlib import Path

# --- CONFIGURATION ---
# Default Windows iTunes Backup Location
APPDATA = os.getenv('APPDATA', '')
LOCALAPPDATA = os.getenv('LOCALAPPDATA', '')

# iTunes saves backups either in Roaming Apple Computer or Local Apple MobileSync
POSSIBLE_BACKUP_PATHS = [
    Path(APPDATA) / "Apple Computer" / "MobileSync" / "Backup",
    Path(LOCALAPPDATA) / "Apple" / "MobileSync" / "Backup"
]

TARGET_DOMAIN = "AppDomain-com.MonsterCouch.Wingspan"
OUTPUT_DIR = Path.home() / "Desktop" / "Wingspan_Extracted_Data"

def locate_latest_backup():
    """Finds the most recent unencrypted iTunes backup directory."""
    for base_path in POSSIBLE_BACKUP_PATHS:
        if base_path.exists():
            backups = [d for d in base_path.iterdir() if d.is_dir()]
            if backups:
                # Sort by modification time to get the absolute newest backup
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return backups[0]
    return None

def extract_wingspan_db(backup_path):
    """Parses Manifest.db to find the real scrambled filenames for Wingspan."""
    manifest_db_path = backup_path / "Manifest.db"
    if not manifest_db_path.exists():
        print(f"❌ Manifest.db missing in backup directory: {backup_path}")
        return None

    print(f"🔍 Analyzing iOS manifest database inside backup: {backup_path.name}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    
    try:
        conn = sqlite3.connect(manifest_db_path)
        cursor = conn.cursor()
        
        # Querying the manifest database mapping files to their hashed on-disk storage name
        # We search specifically for databases (.db, .sqlite) or profile saves (.json, .dat)
        query = """
            SELECT fileID, relativePath 
            FROM Files 
            WHERE domain = ? AND (relativePath LIKE '%.db%' OR relativePath LIKE '%.sqlite%' OR relativePath LIKE '%.json%')
        """
        cursor.execute(query, (TARGET_DOMAIN,))
        matching_files = cursor.fetchall()
        
        if not matching_files:
            print(f"⚠️ No direct database files found in backup for domain: {TARGET_DOMAIN}")
            print("Make sure you completed a local, unencrypted sync in iTunes first.")
            return None

        for file_id, relative_path in matching_files:
            # iOS hashes files by splitting the 40-char string into a 2-char sub-folder name
            folder_prefix = file_id[:2]
            hashed_file_path = backup_path / folder_prefix / file_id
            
            if hashed_file_path.exists():
                clean_name = relative_path.split("/")[-1]
                destination = OUTPUT_DIR / clean_name
                shutil.copy2(hashed_file_path, destination)
                extracted_files.append(destination)
                print(f"   📦 Extracted: {relative_path} -> {clean_name}")
                
        conn.close()
    except Exception as e:
        print(f"💥 Failed parsing backup database file structure: {e}")
        
    return extracted_files

def dump_game_logs(extracted_files):
    """Iterates through extracted files and outputs active tables and stats."""
    if not extracted_files:
        return

    print("\n" + "="*60)
    print("🦅 PRINTING EXTRACTED WINGSPAN LOCAL HISTORY & LOG DATA")
    print("="*60)

    for file_path in extracted_files:
        print(f"\n📄 File: {file_path.name}")
        
        # Check if file is an active SQLite database structure
        if file_path.suffix in ['.db', '.sqlite', '.sqlite3'] or 'database' in file_path.name.lower():
            try:
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if not tables:
                    print("   (Empty Database — No tables found)")
                    continue
                    
                for table in tables:
                    table_name = table[0]
                    print(f"  └── 📊 Table: {table_name}")
                    
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                        rows = cursor.fetchall()
                        for row in rows:
                            print(f"      └── {row}")
                    except Exception as err:
                        print(f"      ❌ Could not print data rows: {err}")
                conn.close()
            except Exception as db_err:
                print(f"   ⚠️ File structurally locked or not an active database: {db_err}")
                
        # If it's a JSON string file mapping data configuration metadata
        elif file_path.suffix == '.json' or file_path.name.endswith('txt'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = f.read(1500) # Print first 1500 characters
                    print(data + ("...\n[Truncated]" if len(data) >= 1500 else ""))
            except Exception as txt_err:
                print(f"   ❌ Could not display content metrics: {txt_err}")

if __name__ == "__main__":
    print("🚀 Running target search parameters...")
    latest_backup = locate_latest_backup()
    
    if latest_backup:
        staged_targets = extract_wingspan_db(latest_backup)
        dump_game_logs(staged_targets)
    else:
        print("❌ Could not find a valid local Apple iTunes Backup path on this machine.")
        print("💡 Action: Plug your iPhone in, open desktop iTunes, and trigger a raw manual backup to 'This Computer' (ensure 'Encrypt local backup' is disabled).")