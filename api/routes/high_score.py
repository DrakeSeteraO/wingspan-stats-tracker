from fastapi import APIRouter, HTTPException
from typing import List
import pymssql
import os
from dotenv import load_dotenv

# Import your Pydantic model from the schema.py file in the root directory
from api.schema import HighScoreReturn

router = APIRouter()

load_dotenv()

# --- Azure SQL Configuration ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# Changed response_model to HighScoreReturn (not List[HighScoreReturn])
@router.get("/api/high-score", response_model=HighScoreReturn, response_model_exclude_none=True)
def get_high_scores(): # Renamed from get_ledger
    
    # 1. Query to get the highest overall score for each individual player
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

    # 2. Query to unpivot the stats and find the single highest score in the group per category
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
                ROW_NUMBER() OVER(PARTITION BY Category ORDER BY Score DESC, date ASC) as rn
            FROM UnpivotedStats
        )
        SELECT name, score, achiever, date FROM RankedRecords WHERE rn = 1;
    """

    try:
        conn = pymssql.connect(
            server=SERVER,
            user=USERNAME,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = conn.cursor(as_dict=True)
        
        # Execute the personal bests query
        cursor.execute(personal_query)
        personal_results = cursor.fetchall()
        
        # Execute the overall records query
        cursor.execute(overall_query)
        overall_results = cursor.fetchall()
        
        conn.close()
        
        # Return a single dictionary that perfectly matches HighScoreReturn
        return {
            "personal": personal_results,
            "overall": overall_results
        }

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))