import json
import os
import pyodbc
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- Azure SQL Configuration ---
load_dotenv()
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('UPLOAD_USERNAME')
PASSWORD = os.getenv('UPLOAD_PASSWORD')
DRIVER = os.getenv('DRIVER')

# File Paths
WINGSPAN_DOCS_DIR = Path("Wingspan/Container/Documents")
CACHE_FILE = Path(".uploaded_games.txt")
SETTINGS_FILE_PATH = WINGSPAN_DOCS_DIR / "Settings.json"

def get_db_connection():
    """Establish a connection to the Azure SQL Database."""
    conn_str = f"DRIVER={DRIVER};SERVER={SERVER};PORT=1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    return pyodbc.connect(conn_str, autocommit=False)

def load_uploaded_cache():
    """Load previously uploaded game IDs into a set for fast lookup."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def mark_as_uploaded(game_id):
    """Append a successfully uploaded game ID to the local cache file."""
    with open(CACHE_FILE, "a") as f:
        f.write(f"{game_id}\n")

def get_true_dates():
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
    return true_game_dates

def upload_to_azure():
    if not WINGSPAN_DOCS_DIR.exists():
        print(f"❌ Error: Cannot locate directory path at '{WINGSPAN_DOCS_DIR}'")
        return

    match_files = list(WINGSPAN_DOCS_DIR.glob("*.nakama-*"))
    if not match_files:
        print("⚠️ No game history files found.")
        return

    # Load our local cache
    uploaded_games = load_uploaded_cache()
    print(f"📂 Found {len(uploaded_games)} previously uploaded games in local cache.")

    # 1. Load the true dates ONCE before the loop starts
    game_dates = get_true_dates()
    print(f"📖 Loaded {len(game_dates)} exact game dates from settings.")

    print("🔌 Connecting to Azure SQL...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        return

    for file_path in match_files:
        try:
            # Extract just the ID first to check our cache before reading the whole file
            temp_id = file_path.name.split('.')[0] 
            
            with open(file_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)

            game_id = game_data.get("MatchId", temp_id)

            # Check cache before doing any database logic
            if game_id in uploaded_games:
                print(f"⏩ Skipping {game_id} (Already in Azure)")
                continue

            # 2. Safely check for the date without triggering a KeyError
            id = game_id.split(".")[0]
            if id in game_dates:
                game_date = game_dates[id]
            else:
                mtime = os.path.getmtime(file_path)
                game_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            players = game_data.get("Players", [])
            scores = game_data.get("Scores", [])
            extensions = game_data.get("Extensions", [])

            # Calculate Winner
            winner_id = "N/A"
            if scores:
                winning_obj = max(scores, key=lambda x: x.get("_ts", -1))
                winner_id = winning_obj.get("_pid", "Unknown ID")
            elif players:
                winning_obj = max(players, key=lambda x: x.get("Score", -1))
                winner_id = winning_obj.get("ID", "Unknown ID")

            # 1. PARENT TABLES
            for p in players:
                p_id = p.get("ID", "Unknown ID")
                p_name = p.get("Name", "Unknown")
                p_username = p.get("Username", p_name)

                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM player_info WHERE player_id = ?)
                    INSERT INTO player_info (player_id, name, username) VALUES (?, ?, ?)
                """, (p_id, p_id, p_name, p_username))

            # 2. CORE GAME TABLE
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM game WHERE game_id = ?)
                INSERT INTO game (game_id, date, player_count, winner_id) VALUES (?, ?, ?, ?)
            """, (game_id, game_id, game_date, len(players), winner_id))

            # 3. CHILD TABLES
            for ext in extensions:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM extension WHERE game_id = ? AND extension_name = ?)
                    INSERT INTO extension (game_id, extension_name) VALUES (?, ?)
                """, (game_id, ext, game_id, ext))

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
                    IF NOT EXISTS (SELECT 1 FROM player_game_stats WHERE player_id = ? AND game_id = ?)
                    INSERT INTO player_game_stats 
                    (player_id, game_id, total, bird, bonus_card, end_of_round_goals, eggs, food_on_cards, tucked_cards, nectar) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s_pid, game_id, s_pid, game_id, total, bird_pts, bonus, eor, eggs, food, tucked, nectar))

            # Commit the transaction to save this specific file to the database
            conn.commit()
            
            # --- CACHE UPDATE ---
            # Now that it's officially in the database, add it to our local tracker
            mark_as_uploaded(game_id)
            uploaded_games.add(game_id)
            
            print(f"✅ Uploaded Game: {game_id}")

        except (json.JSONDecodeError, KeyError) as err:
            print(f"⚠️ Skipping {file_path.name}: Invalid JSON or missing structural keys.")
        except Exception as e:
            # Roll back any partial table inserts if something breaks mid-file
            conn.rollback()
            print(f"❌ Database error on {file_path.name}: {e}")

    cursor.close()
    conn.close()
    print("-" * 80)
    print("🏁 Azure SQL Upload Complete!")

if __name__ == "__main__":
    upload_to_azure()