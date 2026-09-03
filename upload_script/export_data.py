import os
import pyodbc
import csv
import time
from dotenv import load_dotenv

# --- Azure SQL Configuration ---
load_dotenv()
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME') 
PASSWORD = os.getenv('API_PASSWORD')
DRIVER = os.getenv('DRIVER', '{ODBC Driver 18 for SQL Server}') # Updated to match your error

def main():
    print("🔌 Waking up Azure SQL... (This may take 1-2 minutes if the server was paused)")
    
    # Added TrustServerCertificate=yes to bypass ODBC 18 strict SSL requirements
# Port is now attached directly to the SERVER variable with a comma
    conn_str = f"DRIVER={DRIVER};SERVER={SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=yes;"    
    conn = None
    max_retries = 5
    
    # Retry loop to wait for the database to boot
    for attempt in range(max_retries):
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            print("✅ Connected successfully!\n")
            break
        except pyodbc.Error as e:
            if attempt < max_retries - 1:
                print(f"⏳ Database is still booting. Retrying in 30 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(30)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                return

    tables = ['player_info', 'game', 'player_game_stats']

    for table in tables:
        print(f"📦 Extracting {table}...")
        try:
            cursor.execute(f"SELECT * FROM {table}")
            
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            filename = f"{table}_export.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(row)
                    
            print(f"   ↳ Saved {len(rows)} rows to {filename}")
        except Exception as e:
            print(f"   ↳ ❌ Failed to extract {table}: {e}")

    cursor.close()
    conn.close()
    print("\n🏁 Extraction complete. Your data is safely backed up locally!")

if __name__ == "__main__":
    main()