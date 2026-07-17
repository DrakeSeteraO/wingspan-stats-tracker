import os
import pyodbc
import uuid
from datetime import datetime
from dotenv import load_dotenv

# --- Azure SQL Configuration ---
load_dotenv()
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('UPLOAD_USERNAME') # You can swap this to API_USERNAME if needed
PASSWORD = os.getenv('UPLOAD_PASSWORD')
DRIVER = os.getenv('DRIVER', '{ODBC Driver 17 for SQL Server}')

def get_db_connection():
    """Establish a connection to the Azure SQL Database."""
    conn_str = f"DRIVER={DRIVER};SERVER={SERVER};PORT=1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    return pyodbc.connect(conn_str, autocommit=False)

def get_or_create_player(cursor, name):
    """Retrieve an existing player_id or create a new one."""
    cursor.execute("SELECT player_id FROM player_info WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Generate a new UUID for the player if they don't exist
    new_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO player_info (player_id, name, username) 
        VALUES (?, ?, ?)
    """, (new_id, name, name))
    return new_id

def prompt_int(prompt_text):
    """Helper to safely grab integers. Pressing Enter defaults to 0."""
    user_input = input(prompt_text).strip()
    if not user_input:
        return 0
    try:
        return int(user_input)
    except ValueError:
        print("⚠️ Invalid number. Defaulting to 0.")
        return 0

def main():
    print("🔌 Connecting to Azure SQL...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected successfully!\n")
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        return

    while True:
        print("-" * 50)
        print("📝 NEW GAME ENTRY")
        print("-" * 50)
        
        date_input = input("Enter Game Date (YYYY-MM-DD) [or type 'q' to quit]: ").strip()
        if date_input.lower() == 'q':
            break

        try:
            game_date = datetime.strptime(date_input, "%Y-%m-%d").strftime('%Y-%m-%d 00:00:00')
        except ValueError:
            print("⚠️ Invalid date format. Please use YYYY-MM-DD.")
            continue

        try:
            num_players = int(input("Enter number of players: ").strip())
        except ValueError:
            print("⚠️ Please enter a valid number.")
            continue

        game_id = str(uuid.uuid4())
        player_stats = []
        
        for i in range(num_players):
            print(f"\n▶ Player {i+1}")
            name = input("  Name: ").strip()
            
            # Request inputs in the exact order requested
            bird = prompt_int("  Birds points: ")
            bonus = prompt_int("  Bonus Cards points: ")
            eor = prompt_int("  End of Round Goals points: ")
            eggs = prompt_int("  Eggs: ")
            food = prompt_int("  Food on cards: ")
            tucked = prompt_int("  Tucked cards: ")
            
            total = bird + bonus + eor + eggs + food + tucked
            print(f"  [Calculated Total Score: {total}]")
            
            player_id = get_or_create_player(cursor, name)
            
            player_stats.append({
                "player_id": player_id,
                "total": total,
                "bird": bird,
                "bonus": bonus,
                "eor": eor,
                "eggs": eggs,
                "food": food,
                "tucked": tucked,
                "nectar": 0 # Defaulting to 0 to satisfy the DB schema
            })

        # Determine the winner (Player with the highest total)
        winner_id = max(player_stats, key=lambda x: x['total'])['player_id']
        
        try:
            # 1. Insert Core Game Record
            cursor.execute("""
                INSERT INTO game (game_id, date, player_count, winner_id) 
                VALUES (?, ?, ?, ?)
            """, (game_id, game_date, num_players, winner_id))

            # 2. Insert Player Stats
            for p in player_stats:
                cursor.execute("""
                    INSERT INTO player_game_stats 
                    (player_id, game_id, total, bird, bonus_card, end_of_round_goals, eggs, food_on_cards, tucked_cards, nectar) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p['player_id'], game_id, p['total'], p['bird'], p['bonus'], p['eor'], p['eggs'], p['food'], p['tucked'], p['nectar']))
            
            # Commit the transaction to save this specific game
            conn.commit()
            print(f"\n✅ Successfully saved game from {date_input} to the database!")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Database error while saving game: {e}")

        print("\n" + "=" * 50)
        continue_prompt = input("Do you want to enter another game? (y/n): ").strip().lower()
        if continue_prompt != 'y':
            break

    cursor.close()
    conn.close()
    print("🏁 Session ended. Goodbye!")

if __name__ == "__main__":
    main()