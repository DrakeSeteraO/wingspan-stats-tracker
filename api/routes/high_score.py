from fastapi import APIRouter, HTTPException
from typing import List
import pymssql
import os
from dotenv import load_dotenv

from api.schema import HighScoreReturn

router = APIRouter()

load_dotenv()

# --- Azure SQL Configuration ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

@router.get("/api/high-score", response_model=HighScoreReturn, response_model_exclude_none=True)
def get_high_scores():
    
    # 1. Query for Personal Bests (Unchanged)
    personal_query = """
        WITH RankedScores AS (
            SELECT 
                c.name,
                b.total as score,
                CONVERT(varchar, a.date, 23) as date,
                ROW_NUMBER() OVER(PARTITION BY c.name ORDER BY b.total DESC, a.date ASC) as rn
            FROM game a
            JOIN player_game_stats b ON a.game_id = b.game_id
            JOIN player_info c ON b.player_id = c.player_id
            WHERE c.name != 'Unknown' AND b.total IS NOT NULL
        )
        SELECT name, score, date FROM RankedScores WHERE rn = 1;
    """

    # 2. Query for Global Records using RANK() to allow for ties
    overall_query = """
        WITH UnpivotedStats AS (
            SELECT 
                CONVERT(varchar, a.date, 23) as date,
                c.name as achiever,
                Category,
                Score
            FROM game a
            JOIN player_game_stats b ON a.game_id = b.game_id
            JOIN player_info c ON b.player_id = c.player_id
            CROSS APPLY (
                VALUES 
                    ('Total Points', b.total),
                    ('Bird Points', b.bird),
                    ('Bonus Cards', b.bonus_card),
                    ('End of Round Goals', b.end_of_round_goals),
                    ('Eggs', b.eggs),
                    ('Food on Cards', b.food_on_cards),
                    ('Tucked Cards', b.tucked_cards),
                    ('Nectar', b.nectar)
            ) x (Category, Score)
            WHERE c.name != 'Unknown' AND Score IS NOT NULL
        ),
        RankedRecords AS (
            SELECT 
                Category as name,
                Score as score,
                achiever,
                date,
                RANK() OVER(PARTITION BY Category ORDER BY Score DESC) as rnk
            FROM UnpivotedStats
        )
        -- Order by name and date ASC to ensure chronological order for ties
        SELECT name, score, achiever, date FROM RankedRecords WHERE rnk = 1 ORDER BY name, date ASC;
    """

    try:
        conn = pymssql.connect(
            server=SERVER,
            user=USERNAME,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute(personal_query)
        personal_results = cursor.fetchall()
        
        cursor.execute(overall_query)
        overall_results = cursor.fetchall()
        
        conn.close()
        
        # 3. Group the overall records into the new array structure
        grouped_overall = {}
        for row in overall_results:
            cat = row['name']
            if cat not in grouped_overall:
                grouped_overall[cat] = {
                    "name": cat,
                    "score": row['score'],
                    "achievers": []
                }
            # Append the tied player to the achievers array
            grouped_overall[cat]["achievers"].append({
                "name": row['achiever'],
                "date": row['date']
            })
            
        final_overall = list(grouped_overall.values())
        
        return {
            "personal": personal_results,
            "overall": final_overall
        }

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))