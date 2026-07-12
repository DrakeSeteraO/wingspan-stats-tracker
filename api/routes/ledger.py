from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pymssql
import os
import sys
from dotenv import load_dotenv

# Import your Pydantic model from the schema.py file in the root directory
from schema import TrendRequest, TrendRecord

router = APIRouter()

load_dotenv()

# --- Azure SQL Configuration ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# Stack the root route to handle Vercel's file-based routing strip
@router.get("/api/ledger")
def get_ledger():
    
    sql_query = f"""
        SELECT 
            c.name,
            c.username,
            count(*) as games,
            avg(b.total) as average,
            sum(b.total) as total,
            SUM(CASE WHEN a.winner_id = c.player_id THEN 1 ELSE 0 END) as wins,
            ROUND(CAST(SUM(CASE WHEN a.winner_id = c.player_id THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as win_rate
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

        # --- Reformat Data for Frontend Graph ---
        formatted_dict = {}
        
        # Map 'total' to 'totalPoints' to match your frontend example, otherwise use the requested score name
        metric_key = 'totalPoints' if request.score.lower() == 'total' else request.score
        
        for row in results:
            interval = row['time_interval']
            
            # Initialize the interval group if it doesn't exist yet
            if interval not in formatted_dict:
                formatted_dict[interval] = {
                    "date": str(interval),
                    "winner": None,
                    "_max_score": -float('inf'), # Hidden temp key to calculate the winner
                    "results": []
                }
            
            # Handle potential None values from the database
            score = row['calculated_score'] if row['calculated_score'] is not None else 0
            player_name = row['name'] # Using 'name' as requested in your target JSON (e.g., "Wren")
            
            # Append this player's stats to the results array
            formatted_dict[interval]["results"].append({
                "player": player_name,
                metric_key: score
            })
            
            # Dynamically determine the winner for this interval
            if score > formatted_dict[interval]["_max_score"]:
                formatted_dict[interval]["_max_score"] = score
                formatted_dict[interval]["winner"] = player_name
                
        # Strip out the temporary max_score key, convert to a list, and assign sequential IDs
        final_output = []
        
        # enumerate(..., start=1) automatically counts 1, 2, 3... for us
        for index, (interval_key, data) in enumerate(formatted_dict.items(), start=1):
            del data["_max_score"]
            
            # Reconstruct the dictionary so 'id' appears at the top
            final_output.append({
                "id": index,
                **data
            })

        return final_output
   
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))