from fastapi import APIRouter, HTTPException
import pymssql
import os
import math
from datetime import datetime
from dotenv import load_dotenv
from api.schema import OracleReturn, Prediction

router = APIRouter()
load_dotenv()

SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# --- Pure Python Machine Learning Math ---
def simple_linear_regression(x_vals, y_vals):
    """Calculates the line of best fit (slope and intercept) without scikit-learn."""
    n = len(x_vals)
    if n == 0: return 0, 0
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - mean_x) ** 2 for x in x_vals)
    
    slope = numerator / denominator if denominator != 0 else 0
    intercept = mean_y - slope * mean_x
    return slope, intercept

def calculate_rmse(y_actual, y_predicted):
    """Calculates Root Mean Squared Error to determine prediction confidence."""
    if not y_actual: return 0
    mse = sum((act - pred) ** 2 for act, pred in zip(y_actual, y_predicted)) / len(y_actual)
    return math.sqrt(mse)

@router.get("/api/oracle", response_model=OracleReturn, response_model_exclude_none=True)
def get_predictions():
    # Pulled date formatting directly into SQL to avoid Pandas datetime conversions
    sql_query = """
        SELECT p.name, s.total as score, s.eggs, CONVERT(varchar, g.date, 23) as date, g.player_count,
               CASE WHEN g.winner_id = p.player_id THEN 1 ELSE 0 END as is_winner
        FROM player_game_stats s
        JOIN game g ON s.game_id = g.game_id
        JOIN player_info p ON s.player_id = p.player_id
        WHERE p.name != 'Unknown' AND s.total IS NOT NULL
        ORDER BY p.name, g.date ASC
    """

    try:
        conn = pymssql.connect(server=SERVER, user=USERNAME, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        conn.close()

        # Group data by player (Replaces pandas groupby)
        player_data = {}
        for row in rows:
            name = row['name']
            if name not in player_data:
                player_data[name] = []
            player_data[name].append(row)
        
        points_predictions = []
        winner_predictions = []
        egg_predictions = []

        for name, group in player_data.items():
            n_games = len(group)
            if n_games < 5:
                continue

            # --- 1. Feature Engineering ---
            scores = [g['score'] for g in group]
            eggs = [g['eggs'] for g in group]
            dates = [datetime.strptime(g['date'], "%Y-%m-%d") for g in group]
            is_winner = [g['is_winner'] for g in group]
            
            # Calculate rolling averages (window=3)
            rolling_avg_pts = []
            rolling_avg_eggs = []
            for i in range(n_games):
                start_idx = max(0, i - 3)
                rolling_avg_pts.append(sum(scores[start_idx:i]) / max(1, i - start_idx))
                rolling_avg_eggs.append(sum(eggs[start_idx:i]) / max(1, i - start_idx))

            # Future Features for the X_pred matrix
            next_rolling_pts = sum(scores[-3:]) / min(3, len(scores))
            next_rolling_eggs = sum(eggs[-3:]) / min(3, len(eggs))

            # Drop the first game from training since its rolling average is 0
            train_scores = scores[1:]
            train_eggs = eggs[1:]
            train_rolling_pts = rolling_avg_pts[1:]
            train_rolling_eggs = rolling_avg_eggs[1:]

            # ==========================================
            # MODEL 1: Estimated Points (Linear Regression)
            # ==========================================
            slope_pts, intercept_pts = simple_linear_regression(train_rolling_pts, train_scores)
            
            # Inference
            pred_pts = (slope_pts * next_rolling_pts) + intercept_pts
            
            # Confidence (RMSE)
            y_pred_pts = [(slope_pts * x) + intercept_pts for x in train_rolling_pts]
            rmse_pts = calculate_rmse(train_scores, y_pred_pts)
            mean_pts = sum(train_scores) / len(train_scores)
            cv_pts = rmse_pts / mean_pts if mean_pts > 0 else 0
            conf_pts = max(10, min(99, int(100 - (cv_pts * 300))))

            # Quotes
            recent_wins = sum(is_winner[-3:])
            if recent_wins >= 2:
                pts_quote = f"Hot streak: {recent_wins} wins in the last 3 games."
            elif slope_pts < 0: 
                pts_quote = "Struggling to maintain momentum; scores are trending inversely to recent averages."
            elif rmse_pts < 5:
                pts_quote = "Highly predictable engine: extremely low variance in final scores."
            else:
                pts_quote = "Steady climb expected based on recent rolling averages."

            points_predictions.append(Prediction(
                title="Estimated Points Next Game", player=name,
                value=f"{int(round(pred_pts))} pts", confidence=conf_pts, note=pts_quote
            ))

            # ==========================================
            # MODEL 2: Expected Eggs (Linear Regression)
            # ==========================================
            slope_eggs, intercept_eggs = simple_linear_regression(train_rolling_eggs, train_eggs)
            
            pred_eggs = max(0, (slope_eggs * next_rolling_eggs) + intercept_eggs)
            
            y_pred_eggs = [(slope_eggs * x) + intercept_eggs for x in train_rolling_eggs]
            rmse_eggs = calculate_rmse(train_eggs, y_pred_eggs)
            mean_eggs = sum(train_eggs) / len(train_eggs)
            cv_eggs = rmse_eggs / mean_eggs if mean_eggs > 0 else 0
            conf_eggs = max(10, min(99, int(100 - (cv_eggs * 300))))

            if pred_eggs > 18:
                egg_quote = "Egg-laying engine builder supreme."
            elif rmse_eggs < 3:
                egg_quote = "Extremely consistent clutch sizes across recent games."
            elif slope_eggs > 0.8:
                egg_quote = "Improving clutch sizes each week."
            else:
                egg_quote = "Expected to pull standard grassland yields."

            egg_predictions.append(Prediction(
                title="Expected Egg Count", player=name,
                value=f"{int(round(pred_eggs))} eggs", confidence=conf_eggs, note=egg_quote
            ))

            # ==========================================
            # MODEL 3: Predicted Winner (Weighted Probability)
            # ==========================================
            # Pure Python approximation of Logistic Regression using an exponentially decaying win rate
            weights = [1, 1.5, 2, 2.5, 3][:len(is_winner[-5:])]
            weighted_wins = sum(w * act for w, act in zip(weights, is_winner[-5:]))
            prob_win = weighted_wins / sum(weights) if sum(weights) > 0 else 0
            
            win_pct = int(prob_win * 100)

            if win_pct > 40:
                win_quote = "Strong favorite based on dominant recent scoring."
            elif recent_wins > 0 and win_pct > 25:
                win_quote = "Momentum from recent victories is heavily factoring in."
            elif win_pct < 15:
                win_quote = "The quiet underdog — watch the wetlands."
            else:
                win_quote = "Solid mid-table probability for the upcoming match."

            winner_predictions.append(Prediction(
                title="Predicted Winner", player=name,
                value=f"{win_pct}%", confidence=win_pct, note=win_quote
            ))

        winner_predictions.sort(key=lambda x: x.confidence, reverse=True)

        return OracleReturn(
            nextGamePoints=points_predictions,
            nextWinner=winner_predictions,
            eggCount=egg_predictions
        )

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))