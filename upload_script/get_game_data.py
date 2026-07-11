import json
import os
from datetime import datetime
from pathlib import Path

# Base directory targeting the extracted folder structure
WINGSPAN_DOCS_DIR = Path("Wingspan/Container/Documents")

def parse_wingspan_games():
    # Verify the path exists before attempting loop execution
    if not WINGSPAN_DOCS_DIR.exists():
        print(f"❌ Error: Cannot locate directory path at '{WINGSPAN_DOCS_DIR}'")
        print("Please ensure your extracted folder matches the expected file tree.")
        return

    # Grab all matching files containing game histories (.nakama files)
    match_files = list(WINGSPAN_DOCS_DIR.glob("*.nakama-*"))

    if not match_files:
        print(f"⚠️ No game history files found in {WINGSPAN_DOCS_DIR}")
        return

    print("=" * 80)
    print(f"🦅 PROCESSING {len(match_files)} WINGSPAN MATCHES")
    print("=" * 80)

    for file_path in match_files:
        try:
            # Extract file modification time to capture game date
            mtime = os.path.getmtime(file_path)
            game_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            with open(file_path, "r", encoding="utf-8") as f:
                game_data = json.load(f)

            # Extract required architectural keys safely
            game_id = game_data.get("MatchId", file_path.name)
            players = game_data.get("Players", [])
            total_players = len(players)
            scores = game_data.get("Scores", [])

            # Reconstruct the winner data directly from the calculated end-scores
            winner_id = "N/A"
            winner_score = -1

            if scores:
                # Find the maximum total score array entry '_ts'
                winning_obj = max(scores, key=lambda x: x.get("_ts", -1))
                winner_score = winning_obj.get("_ts", 0)
                winner_id = winning_obj.get("_pid", "Unknown ID")
            elif players:
                # Fallback to base score logic check if nested explicitly
                winning_obj = max(players, key=lambda x: x.get("Score", -1))
                winner_score = winning_obj.get("Score", 0)
                winner_id = winning_obj.get("ID", "Unknown ID")

            # Clean output execution loop printing blocks
            print(f"🎯 Game ID:       {game_id}")
            print(f"📅 Date:          {game_date}")
            print(f"👥 Total Players: {total_players}")
            print(f"🏆 Winner ID:     {winner_id}")
            print(f"📊 Winner Score:  {winner_score}")
            print("-" * 80)

        except (json.JSONDecodeError, KeyError, PermissionError) as err:
            # Silently catch/skip systemic non-json system documents (like 'Settings')
            print(f"⏩ Skipping corrupted/system configuration file '{file_path.name}': {err}")
            print("-" * 80)

if __name__ == "__main__":
    parse_wingspan_games()