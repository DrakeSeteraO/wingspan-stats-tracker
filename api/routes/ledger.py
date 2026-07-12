from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pymssql
import os
import sys
from dotenv import load_dotenv

# Import your Pydantic model from the schema.py file in the root directory
from api.schema import LedgerData

router = APIRouter()

load_dotenv()

# --- Azure SQL Configuration ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# Stack the root route to handle Vercel's file-based routing strip
@router.get("/api/ledger", response_model=List[LedgerData], response_model_exclude_none=True)
def get_ledger():
    
    sql_query = f"""
        SELECT 
            c.name,
            c.username,
            count(*) as games,
            avg(b.total) as average,
            sum(b.total) as total,
            SUM(CASE WHEN a.winner_id = c.player_id THEN 1 ELSE 0 END) as wins,
            ROUND(CAST(SUM(CASE WHEN a.winner_id = c.player_id THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as win_rate,
            ROUND(CAST(SUM(CASE WHEN a.player_count = 2 AND a.winner_id = c.player_id THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN a.player_count = 2 THEN 1 ELSE 0 END), 0) * 100, 1) as win_rate_2p,
            ROUND(CAST(SUM(CASE WHEN a.player_count = 3 AND a.winner_id = c.player_id THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN a.player_count = 3 THEN 1 ELSE 0 END), 0) * 100, 1) as win_rate_3p,
            ROUND(CAST(SUM(CASE WHEN a.player_count = 4 AND a.winner_id = c.player_id THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(SUM(CASE WHEN a.player_count = 4 THEN 1 ELSE 0 END), 0) * 100, 1) as win_rate_4p
        FROM
            game a,
            player_game_stats b, 
            player_info c
        WHERE
            a.game_id = b.game_id
            AND b.player_id = c.player_id
            AND c.name != 'Unknown'
        GROUP BY
            c.player_id,
            c.name,
            c.username;
    """

    try:
        conn = pymssql.connect(
            server=SERVER,
            user=USERNAME,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = conn.cursor(as_dict=True)
        cursor.execute(sql_query)
            
        results = cursor.fetchall()
        conn.close()
        return results

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))