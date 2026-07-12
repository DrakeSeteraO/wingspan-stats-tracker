import json
import os
import pyodbc
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

# --- Azure SQL Configuration (Powered by .env) ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('UPLOAD_USERNAME')
PASSWORD = os.getenv('UPLOAD_PASSWORD')
DRIVER = os.getenv('DRIVER')

# File Paths
WINGSPAN_DOCS_DIR = Path("Wingspan/Container/Documents")

# UPDATE THIS to match the exact name of your settings file
SETTINGS_FILE_PATH = WINGSPAN_DOCS_DIR / "Settings.json" 

def get_db_connection():
    """Establish a connection to the Azure SQL Database."""
    conn_str = f"DRIVER={DRIVER};SERVER={SERVER};PORT=1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    return pyodbc.connect(conn_str, autocommit=False)

def update_azure_data():
    if not WINGSPAN_DOCS_DIR.exists():
        print(f"❌ Error: Cannot locate directory path at '{WINGSPAN_DOCS_DIR}'")
        return

    match_files = list(WINGSPAN_DOCS_DIR.glob("*.nakama-*"))
    if not match_files:
        print("⚠️ No game history files found.")
        return

    # 1. Load the true timestamps from the Settings file
    true_game_dates = {}
    if SETTINGS_FILE_PATH.exists():
        with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as sf:
            settings_data = json.load(sf)
            for archive in settings_data.get("ArchivedGameSaves", []):
                match_id_full = archive.get("MatchId", "")
                # Extract just the UUID prefix (e.g., "d582585b-e59f-4b4a-a4bf-e0d7888924dc")
                base_id = match_id_full.split('.')[0] 
                played_ts = archive.get("GamePlayedDate")
                
                if base_id and played_ts:
                    # Convert the Unix timestamp to a SQL-friendly datetime string
                    true_game_dates[base_id] = datetime.fromtimestamp(played_ts).strftime('%Y-%m-%d %H:%M:%S')
        print(f"📖 Loaded {len(true_game_dates)} exact game dates from settings.")
    else:
        print(f"⚠️ Settings file not found at {SETTINGS_FILE_PATH}. Will fallback to file properties.")

    print("🔌 Connecting to Azure SQL for Data Correction...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        return

    for file_path in match_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)

            # Isolate the UUID from the filename (e.g., UUID.nakama-0)
            temp_id = file_path.name.split('.')[0] 
            game_id = game_data.get("MatchId", temp_id)
            
            # 2. Get the true date from the dictionary, or fallback to file modified time
            if temp_id in true_game_dates:
                game_date = true_game_dates[temp_id]
            else:
                mtime = os.path.getmtime(file_path)
                game_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            players = game_data.get("Players", [])
            scores = game_data.get("Scores", [])

            # Calculate Winner
            winner_id = "N/A"
            if scores:
                winning_obj = max(scores, key=lambda x: x.get("_ts", -1))
                winner_id = winning_obj.get("_pid", "Unknown ID")
            elif players:
                winning_obj = max(players, key=lambda x: x.get("Score", -1))
                winner_id = winning_obj.get("ID", "Unknown ID")

            # ---------------------------------------------------------
            # UPDATE Player Info
            # ---------------------------------------------------------
            for p in players:
                p_id = p.get("ID", "Unknown ID")
                p_username = p.get("Username", "Unknown")

                cursor.execute("""
                    UPDATE player_info 
                    SET username = ? 
                    WHERE player_id = ?
                """, (p_username, p_id))

            # ---------------------------------------------------------
            # UPDATE Game
            # ---------------------------------------------------------
            cursor.execute("""
                UPDATE game 
                SET date = ?, player_count = ?, winner_id = ? 
                WHERE game_id = ?
            """, (game_date, len(players), winner_id, game_id))

            # ---------------------------------------------------------
            # UPDATE Player Game Stats
            # ---------------------------------------------------------
            for score_data in scores:
                s_pid = score_data.get("_pid", "Unknown ID")
                
                total = score_data.get("_ts", 0)
                bird_pts = score_data.get("_bp", 0)
                bonus = score_data.get("_bcp", 0)
                eor = score_data.get("_gp", 0)
                eggs = score_data.get("_ep", 0)
                food = score_data.get("_cfp", 0)
                tucked = score_data.get("_tcp", 0)
                nectar = score_data.get("_snp", 0)

                cursor.execute("""
                    UPDATE player_game_stats 
                    SET total = ?, bird = ?, bonus_card = ?, end_of_round_goals = ?, 
                        eggs = ?, food_on_cards = ?, tucked_cards = ?, nectar = ?
                    WHERE player_id = ? AND game_id = ?
                """, (total, bird_pts, bonus, eor, eggs, food, tucked, nectar, s_pid, game_id))

            # Commit the transaction to save the updates for this file
            conn.commit()
            print(f"🔄 Corrected Data for Game: {game_id} (Date: {game_date})")

        except (json.JSONDecodeError, KeyError):
            print(f"⚠️ Skipping {file_path.name}: Invalid JSON or missing structural keys.")
        except Exception as e:
            # Roll back if something breaks mid-file
            conn.rollback()
            print(f"❌ Database error on {file_path.name}: {e}")

    cursor.close()
    conn.close()
    print("-" * 80)
    print("🏁 Azure SQL Data Correction Complete!")

if __name__ == "__main__":
    update_azure_data()