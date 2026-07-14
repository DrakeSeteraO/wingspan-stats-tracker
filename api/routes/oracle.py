from fastapi import APIRouter, HTTPException
import pymssql
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression, LogisticRegression
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
    # Added 's.eggs' to the SQL query to pull the necessary data
    sql_query = """
        SELECT p.name, s.total as score, s.eggs, g.date, g.player_count,
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

        df = pd.DataFrame(rows)
        if df.empty:
            return OracleReturn(nextGamePoints=[], nextWinner=[], eggCount=[])

        df['date'] = pd.to_datetime(df['date'])
        
        points_predictions = []
        winner_predictions = []
        egg_predictions = []

        for name, group in df.groupby('name'):
            group = group.copy().reset_index(drop=True)
            n_games = len(group)
            
            if n_games < 5:
                continue

            # --- 1. Feature Engineering ---
            group['rolling_avg_pts'] = group['score'].shift(1).rolling(window=3, min_periods=1).mean()
            group['rolling_avg_eggs'] = group['eggs'].shift(1).rolling(window=3, min_periods=1).mean()
            group['days_since_last'] = group['date'].diff().dt.days.fillna(0)
            
            train_df = group.dropna().copy()
            if len(train_df) < 4:
                continue
                
            # Future Features for the X_pred matrix
            next_player_count = int(group['player_count'].mode()[0])
            next_rolling_pts = group['score'].tail(3).mean()
            next_rolling_eggs = group['eggs'].tail(3).mean()
            days_since_last = (datetime.now() - group['date'].iloc[-1]).days

            X_base = train_df[['player_count', 'days_since_last']]

            # ==========================================
            # MODEL 1: Estimated Points (Linear Regression)
            # ==========================================
            X_pts = X_base.copy()
            X_pts['rolling_avg_pts'] = train_df['rolling_avg_pts']
            y_pts = train_df['score']

            model_pts = LinearRegression().fit(X_pts, y_pts)
            
            X_pred_pts = pd.DataFrame({
                'player_count': [next_player_count],
                'days_since_last': [days_since_last],
                'rolling_avg_pts': [next_rolling_pts]
            })
            
            pred_pts = model_pts.predict(X_pred_pts)[0]
            rmse_pts = math.sqrt(np.mean((y_pts - model_pts.predict(X_pts)) ** 2))
            cv_pts = rmse_pts / y_pts.mean() if y_pts.mean() > 0 else 0
            conf_pts = max(10, min(99, int(100 - (cv_pts * 300))))

            recent_wins = group['is_winner'].tail(3).sum()
            if recent_wins >= 2:
                pts_quote = f"Hot streak: {recent_wins} wins in the last 3 games."
            elif model_pts.coef_[0] < -3.0: 
                pts_quote = f"Board congestion penalty: struggles statistically in {next_player_count}-player matches."
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
            X_eggs = X_base.copy()
            X_eggs['rolling_avg_eggs'] = train_df['rolling_avg_eggs']
            y_eggs = train_df['eggs']

            model_eggs = LinearRegression().fit(X_eggs, y_eggs)
            
            X_pred_eggs = pd.DataFrame({
                'player_count': [next_player_count],
                'days_since_last': [days_since_last],
                'rolling_avg_eggs': [next_rolling_eggs]
            })
            
            pred_eggs = max(0, model_eggs.predict(X_pred_eggs)[0]) # Eggs can't be negative
            rmse_eggs = math.sqrt(np.mean((y_eggs - model_eggs.predict(X_eggs)) ** 2))
            cv_eggs = rmse_eggs / y_eggs.mean() if y_eggs.mean() > 0 else 0
            conf_eggs = max(10, min(99, int(100 - (cv_eggs * 300))))

            if pred_eggs > 18:
                egg_quote = "Egg-laying engine builder supreme."
            elif rmse_eggs < 3:
                egg_quote = "Extremely consistent clutch sizes across recent games."
            elif model_eggs.coef_[2] > 0.8: # Positive correlation with rolling average
                egg_quote = "Improving clutch sizes each week."
            else:
                egg_quote = "Expected to pull standard grassland yields."

            egg_predictions.append(Prediction(
                title="Expected Egg Count", player=name,
                value=f"{int(round(pred_eggs))} eggs", confidence=conf_eggs, note=egg_quote
            ))

            # ==========================================
            # MODEL 3: Predicted Winner (Logistic Regression)
            # ==========================================
            y_win = train_df['is_winner']
            
            # Logistic Regression crashes if a player has NEVER won or ALWAYS won in the dataset
            # We must verify there are at least two distinct classes (0 and 1) before fitting
            if len(y_win.unique()) > 1:
                # class_weight='balanced' helps counteract the fact that players lose more games than they win
                model_win = LogisticRegression(class_weight='balanced').fit(X_pts, y_win)
                # Extract the probability of class '1' (Winning)
                prob_win = model_win.predict_proba(X_pred_pts)[0][1]
            else:
                # If they've never won, we assign a baseline 0% (or 100% if they've never lost)
                prob_win = float(y_win.iloc[0])

            win_pct = int(prob_win * 100)

            if win_pct > 40:
                win_quote = "Strong favorite based on dominant recent scoring."
            elif recent_wins > 0 and win_pct > 25:
                win_quote = "Momentum from recent victories is heavily factoring in."
            elif win_pct < 15:
                win_quote = "The quiet underdog — watch the wetlands."
            else:
                win_quote = "Solid mid-table probability for the upcoming match."

            # We map the percentage directly to both the display value and the progress bar
            winner_predictions.append(Prediction(
                title="Predicted Winner", player=name,
                value=f"{win_pct}%", confidence=win_pct, note=win_quote
            ))

        # We sort the winner predictions so the player with the highest probability appears first
        winner_predictions.sort(key=lambda x: x.confidence, reverse=True)

        return OracleReturn(
            nextGamePoints=points_predictions,
            nextWinner=winner_predictions,
            eggCount=egg_predictions
        )

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))