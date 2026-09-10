import json
import os
import psycopg2
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

# --- PostgreSQL Configuration (Powered by .env) ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE', 'wingspan_db')
USERNAME = os.getenv('UPLOAD_USERNAME')
PASSWORD = os.getenv('UPLOAD_PASSWORD')

# File Paths
WINGSPAN_DOCS_DIR = Path("Wingspan/Container/Documents")

def get_db_connection():
    """Establish a connection to the PostgreSQL Database."""
    return psycopg2.connect(host=SERVER, dbname=DATABASE, user=USERNAME, password=PASSWORD)

def update_postgres_data():
    if not WINGSPAN_DOCS_DIR.exists():
        print(f"❌ Error: Cannot locate directory path at '{WINGSPAN_DOCS_DIR}'")
        return

    match_files = list(WINGSPAN_DOCS_DIR.glob("*.nakama-*"))
    if not match_files:
        print("⚠️ No game history files found.")
        return

    print("🔌 Connecting to PostgreSQL for Data Correction...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    for file_path in match_files:
        try:
            mtime = os.path.getmtime(file_path)
            game_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            with open(file_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)

            # Assuming the filename format is something like UUID.nakama-0
            temp_id = file_path.name.split('.')[0] 
            game_id = game_data.get("MatchId", temp_id)

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
                    SET username = %s 
                    WHERE player_id = %s
                """, ( p_username, p_id))

            # ---------------------------------------------------------
            # UPDATE Game
            # ---------------------------------------------------------
            cursor.execute("""
                UPDATE game 
                SET date = %s, player_count = %s, winner_id = %s 
                WHERE game_id = %s
            """, (game_date, len(players), winner_id, game_id))

            # Note: The 'extension' table ONLY contains primary keys (game_id, extension_name).
            # Because there are no other columns to update, we completely skip it here. 
            # If a row exists, it's already correct. If it doesn't, an UPDATE wouldn't fix it anyway.

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
                    SET total = %s, bird = %s, bonus_card = %s, end_of_round_goals = %s, 
                        eggs = %s, food_on_cards = %s, tucked_cards = %s, nectar = %s
                    WHERE player_id = %s AND game_id = %s
                """, (total, bird_pts, bonus, eor, eggs, food, tucked, nectar, s_pid, game_id))

            # Commit the transaction to save the updates for this file
            conn.commit()
            print(f"🔄 Corrected Data for Game: {game_id}")

        except (json.JSONDecodeError, KeyError):
            print(f"⚠️ Skipping {file_path.name}: Invalid JSON or missing structural keys.")
        except Exception as e:
            # Roll back if something breaks mid-file
            conn.rollback()
            print(f"❌ Database error on {file_path.name}: {e}")

    cursor.close()
    conn.close()
    print("-" * 80)
    print("🏁 PostgreSQL Data Correction Complete!")

if __name__ == "__main__":
    update_postgres_data()