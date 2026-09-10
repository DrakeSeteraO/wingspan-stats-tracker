import os
import psycopg2
import csv
import time
from dotenv import load_dotenv

# --- PostgreSQL Configuration ---
load_dotenv()
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE', 'wingspan_db')
USERNAME = os.getenv('API_USERNAME') 
PASSWORD = os.getenv('API_PASSWORD')

def main():
    print("🔌 Connecting to PostgreSQL...")
    
    conn = None
    max_retries = 5
    
    # Retry loop to wait for the database connection
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(host=SERVER, dbname=DATABASE, user=USERNAME, password=PASSWORD)
            cursor = conn.cursor()
            print("✅ Connected successfully!\n")
            break
        except psycopg2.Error as e:
            if attempt < max_retries - 1:
                print(f"⏳ Database is not ready. Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                return

    tables = ['player_info', 'game', 'player_game_stats']

    for table in tables:
        print(f"📦 Extracting {table}...")
        try:
            cursor.execute(f"SELECT * FROM {table}")
            
            # Extract column headers dynamically
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