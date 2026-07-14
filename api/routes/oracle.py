from fastapi import APIRouter, HTTPException
import pymssql
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
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
    # Fetch all scores chronologically to safely build rolling features
    sql_query = """
        SELECT p.name, s.total as score, g.date, g.player_count,
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

        # Ensure dates are datetime objects
        df['date'] = pd.to_datetime(df['date'])
        
        points_predictions = []

        for name, group in df.groupby('name'):
            group = group.copy().reset_index(drop=True)
            n_games = len(group)
            
            # Need a minimum threshold of games to train a regression model without overfitting
            if n_games < 5:
                continue

            # --- 1. Feature Engineering ---
            # Rolling average of the previous 3 games
            group['rolling_avg'] = group['score'].shift(1).rolling(window=3, min_periods=1).mean()
            
            # Days since the last game (Rest period)
            group['days_since_last'] = group['date'].diff().dt.days.fillna(0)
            
            # Drop the first row since it won't have a valid rolling average
            train_df = group.dropna().copy()
            
            X = train_df[['player_count', 'rolling_avg', 'days_since_last']]
            y = train_df['score']

            # --- 2. Model Training ---
            model = LinearRegression()
            model.fit(X, y)
            
            coefficients = model.coef_
            
            # --- 3. Inference for the Next Game ---
            # Assume the next game matches their mode player count
            next_player_count = int(group['player_count'].mode()[0])
            next_rolling_avg = group['score'].tail(3).mean()
            
            # Assume the game is happening today to calculate rest period
            days_since_last = (datetime.now() - group['date'].iloc[-1]).days
            
            X_pred = pd.DataFrame({
                'player_count': [next_player_count],
                'rolling_avg': [next_rolling_avg],
                'days_since_last': [days_since_last]
            })
            
            predicted_score = model.predict(X_pred)[0]

            # --- 4. Confidence Calculation (Standard Error) ---
            # Calculate the Root Mean Squared Error (RMSE) on the training set
            predictions = model.predict(X)
            rmse = math.sqrt(np.mean((y - predictions) ** 2))
            mean_score = y.mean()
            
            # Coefficient of Variation based on the model's residual error
            cv = rmse / mean_score if mean_score > 0 else 0
            # Scale it to a percentage (tighter error = higher confidence)
            confidence = max(10, min(99, int(100 - (cv * 300))))

            # --- 5. Data-Driven Dynamic Quotes ---
            recent_wins = group['is_winner'].tail(3).sum()
            
            # Analyze the model weights to generate a personalized quote
            if recent_wins >= 2:
                quote = f"Hot streak: {recent_wins} wins in the last 3 games."
            elif coefficients[0] < -3.0: 
                # player_count feature is highly negative
                quote = f"Board congestion penalty: struggles statistically in {next_player_count}-player matches."
            elif coefficients[0] > 3.0:
                quote = "Thrives in chaos: statistically performs better with more opponents."
            elif coefficients[2] > 0.5 and days_since_last > 14:
                # days_since_last is highly positive
                quote = "Well-rested: historical data shows strong performance after a break."
            elif rmse < 5:
                quote = "Highly predictable engine: extremely low variance in final scores."
            else:
                quote = "Steady climb expected based on recent rolling averages."

            points_predictions.append(Prediction(
                title="Estimated Points Next Game",
                player=name,
                value=f"{int(round(predicted_score))} pts",
                confidence=confidence,
                note=quote
            ))

        return OracleReturn(
            nextGamePoints=points_predictions,
            nextWinner=[],
            eggCount=[]
        )

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))