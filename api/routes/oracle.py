from fastapi import APIRouter, HTTPException
import pymssql
import os
import math
from dotenv import load_dotenv
from api.schema import OracleReturn, Prediction

router = APIRouter()
load_dotenv()

SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

@router.get("/api/oracle", response_model=OracleReturn, response_model_exclude_none=True)
def get_predictions():
    # Fetch all scores chronologically, noting if the player won
    sql_query = """
        SELECT p.name, s.total as score, g.date, 
               CASE WHEN g.winner_id = p.player_id THEN 1 ELSE 0 END as is_winner
        FROM player_game_stats s
        JOIN game g ON s.game_id = g.game_id
        JOIN player_info p ON s.player_id = p.player_id
        WHERE p.name != 'Unknown' AND s.total IS NOT NULL
        ORDER BY p.name, g.date DESC
    """

    try:
        conn = pymssql.connect(server=SERVER, user=USERNAME, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        conn.close()

        # Group data by player
        player_data = {}
        for row in rows:
            name = row['name']
            if name not in player_data:
                player_data[name] = []
            player_data[name].append(row)

        points_predictions = []

        for name, games_desc in player_data.items():
            if not games_desc: continue
            
            # Extract scores in chronological order (oldest to newest) for WMA
            scores = [g['score'] for g in reversed(games_desc)]
            n_games = len(scores)
            
            # --- 1. Statistical Calculations ---
            mean = sum(scores) / n_games
            variance = sum((x - mean) ** 2 for x in scores) / n_games
            stdev = math.sqrt(variance)
            
            # Weighted Moving Average (Leaning on the last 5 games)
            recent_scores = scores[-5:]
            weights = [1, 2, 3, 4, 5][:len(recent_scores)]
            predicted_score = sum(s * w for s, w in zip(recent_scores, weights)) / sum(weights)
            
            # Confidence based on Coefficient of Variation (capped between 10% and 99%)
            cv = stdev / mean if mean else 0
            confidence = max(10, min(99, int(100 - (cv * 200))))

            # --- 2. Dynamic Quote Generation ---
            recent_wins = sum(1 for g in games_desc[:3] if g['is_winner'])
            
            if recent_wins >= 2:
                quote = f"Hot streak: {recent_wins} wins in the last 3 games."
            elif n_games >= 3 and scores[-1] > scores[-2] > scores[-3]:
                quote = "Steady climb over the last three matches."
            elif stdev < 5:
                quote = "Unshakably consistent scoring pattern."
            elif scores[-1] < mean - 10:
                quote = "Looking to bounce back from a rough previous game."
            else:
                quote = "Trending closely to their historical average."

            points_predictions.append(Prediction(
                title="Estimated Points Next Game",
                player=name,
                value=f"{int(predicted_score)} pts",
                confidence=confidence,
                note=quote
            ))

        # Returning empty lists for Winner and Egg logic until you implement those algorithms
        return OracleReturn(
            nextGamePoints=points_predictions,
            nextWinner=[],
            eggCount=[]
        )

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))