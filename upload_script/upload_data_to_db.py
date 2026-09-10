import json
import os
import psycopg2
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# --- PostgreSQL Configuration ---
load_dotenv()
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE', 'wingspan_db')
USERNAME = os.getenv('UPLOAD_USERNAME')
PASSWORD = os.getenv('UPLOAD_PASSWORD')

WINGSPAN_DOCS_DIR = Path("Wingspan/Container/Documents")
CACHE_FILE = Path(".uploaded_games.txt")
SETTINGS_FILE_PATH = WINGSPAN_DOCS_DIR / "Settings.json"

def get_db_connection():
    """Establish a connection to the PostgreSQL Database."""
    return psycopg2.connect(host=SERVER, dbname=DATABASE, user=USERNAME, password=PASSWORD)

def load_uploaded_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def mark_as_uploaded(game_id):
    with open(CACHE_FILE, "a") as f:
        f.write(f"{game_id}\n")

def get_true_dates():
    true_game_dates = {}
    if SETTINGS_FILE_PATH.exists():
        with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as sf:
            settings_data = json.load(sf)
            for archive in settings_data.get("ArchivedGameSaves", []):
                match_id_full = archive.get("MatchId", "")
                base_id = match_id_full.split('.')[0] 
                played_ts = archive.get("GamePlayedDate")
                
                if base_id and played_ts:
                    true_game_dates[base_id] = datetime.fromtimestamp(played_ts).strftime('%Y-%m-%d %H:%M:%S')
    return true_game_dates

def upload_to_postgres():
    if not WINGSPAN_DOCS_DIR.exists():
        print(f"❌ Error: Cannot locate directory path at '{WINGSPAN_DOCS_DIR}'")
        return

    match_files = list(WINGSPAN_DOCS_DIR.glob("*.nakama-*"))
    if not match_files:
        print("⚠️ No game history files found.")
        return

    uploaded_games = load_uploaded_cache()
    print(f"📂 Found {len(uploaded_games)} previously uploaded games in local cache.")

    game_dates = get_true_dates()
    print(f"📖 Loaded {len(game_dates)} exact game dates from settings.")

    print("🔌 Connecting to PostgreSQL...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    for file_path in match_files:
        try:
            temp_id = file_path.name.split('.')[0] 
            
            with open(file_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)

            game_id = game_data.get("MatchId", temp_id)

            if game_id in uploaded_games:
                print(f"⏩ Skipping {game_id} (Already in PostgreSQL)")
                continue

            id = game_id.split(".")[0]
            if id in game_dates:
                game_date = game_dates[id]
            else:
                mtime = os.path.getmtime(file_path)
                game_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            players = game_data.get("Players", [])
            scores = game_data.get("Scores", [])
            extensions = game_data.get("Extensions", [])

            winner_id = "N/A"
            if scores:
                winning_obj = max(scores, key=lambda x: x.get("_ts", -1))
                winner_id = winning_obj.get("_pid", "Unknown ID")
            elif players:
                winning_obj = max(players, key=lambda x: x.get("Score", -1))
                winner_id = winning_obj.get("ID", "Unknown ID")

            # 1. PARENT TABLES (Converted to ON CONFLICT)
            for p in players:
                p_id = p.get("ID", "Unknown ID")
                p_name = p.get("Name", "Unknown")
                p_username = p.get("Username", p_name)

                cursor.execute("""
                    INSERT INTO player_info (player_id, name, username) VALUES (%s, %s, %s)
                    ON CONFLICT (player_id) DO NOTHING
                """, (p_id, p_name, p_username))

            # 2. CORE GAME TABLE (Converted to ON CONFLICT)
            cursor.execute("""
                INSERT INTO game (game_id, date, player_count, winner_id) VALUES (%s, %s, %s, %s)
                ON CONFLICT (game_id) DO NOTHING
            """, (game_id, game_date, len(players), winner_id))

            # 3. CHILD TABLES (Converted to WHERE NOT EXISTS)
            # (Assuming extension table exists; if not, comment this block out)
            for ext in extensions:
                cursor.execute("""
                    INSERT INTO extension (game_id, extension_name)
                    SELECT %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM extension WHERE game_id = %s AND extension_name = %s)
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
                    INSERT INTO player_game_stats 
                    (player_id, game_id, total, bird, bonus_card, end_of_round_goals, eggs, food_on_cards, tucked_cards, nectar) 
                    SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM player_game_stats WHERE player_id = %s AND game_id = %s
                    )
                """, (s_pid, game_id, total, bird_pts, bonus, eor, eggs, food, tucked, nectar, s_pid, game_id))

            conn.commit()
            
            mark_as_uploaded(game_id)
            uploaded_games.add(game_id)
            
            print(f"✅ Uploaded Game: {game_id}")

        except (json.JSONDecodeError, KeyError) as err:
            print(f"⚠️ Skipping {file_path.name}: Invalid JSON or missing structural keys.")
        except Exception as e:
            conn.rollback()
            print(f"❌ Database error on {file_path.name}: {e}")

    cursor.close()
    conn.close()
    print("-" * 80)
    print("🏁 PostgreSQL Upload Complete!")

if __name__ == "__main__":
    upload_to_postgres()