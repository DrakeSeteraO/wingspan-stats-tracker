from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

# Import your Pydantic model from the schema.py file in the root directory
from api.schema import TrendRequest, TrendRecord

router = APIRouter()

load_dotenv()

SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# Stack the root route to handle Vercel's file-based routing strip
@router.post("/api/trend", response_model=List[TrendRecord], response_model_exclude_none=True)
def get_stats(request: TrendRequest):
    
    # Security Allowlists
    allowed_scores = {
        'total': 'total',
        'bird': 'bird',
        'bonus_card': 'bonus_card',
        'end_of_round_goals':'end_of_round_goals',
        'eggs': 'eggs',
        'food': 'food_on_cards',
        'tucked': 'tucked_cards',
        'nectar': 'nectar',
        'wins': 'wins'
    }

    allowed_handlers = {
        'sum': 'SUM',
        'avg': 'AVG',
        'min': 'MIN',
        'max': 'MAX',
        'cumulative': 'SUM'
    }

    allowed_intervals = {
        'game': 'g.game_id',
        'day': 'CAST(g.date AS DATE)',
        'week': "CAST(DATE_TRUNC('week', g.date) AS DATE)",
        'month': "TO_CHAR(g.date, 'YYYY-MM')",
        'year': "TO_CHAR(g.date, 'YYYY')",
        'all': "'All-Time'" 
    }

    # Validate Inputs
    safe_score = allowed_scores.get(request.score.lower(), 'total')
    safe_handler = allowed_handlers.get(request.handler.lower(), 'SUM')
    
    # Extract the interval explicitly so we can test it for our logic
    req_interval = request.interval.lower()
    safe_group_interval = allowed_intervals.get(req_interval, 'g.game_id')

    if not safe_score or not safe_handler or not safe_group_interval:
        raise HTTPException(status_code=400, detail="Invalid score, handler, or interval parameter.")

    # --- Generate the Sequential Numbering for Games ---
    if req_interval == 'game':
        safe_select_interval = "ROW_NUMBER() OVER(PARTITION BY p.username ORDER BY MAX(g.date))"
    else:
        safe_select_interval = safe_group_interval

    # --- Determine Table Source ---
    if safe_score == 'wins':
        table_source = """(
            SELECT *, 
                   CASE WHEN RANK() OVER(PARTITION BY game_id ORDER BY total DESC) = 1 THEN 1 ELSE 0 END AS wins 
            FROM player_game_stats
        ) s"""
    else:
        table_source = "player_game_stats s"
    
    # Construct the Dynamic Query and Conditional WHERE Clause
    where_clause = ""
    query_params = ()

    if request.players:
        placeholders = ", ".join(["%s"] * len(request.players))
        where_clause = f"WHERE p.name IN ({placeholders})"
        query_params = tuple(request.players)
        
    if req_interval in ['all', 'all-time']:
        group_by_clause = "GROUP BY p.username, p.name"
        order_by_clause = "ORDER BY p.username"
    else:
        group_by_clause = f"GROUP BY {safe_group_interval}, p.username, p.name"
        order_by_clause = "ORDER BY time_interval"
    
    sql_query = f"""
    SELECT 
        {safe_select_interval} AS time_interval,
        p.username,
        p.name,
        {safe_handler}(s.{safe_score}) AS calculated_score
    FROM {table_source}
    JOIN game g ON s.game_id = g.game_id
    JOIN player_info p ON s.player_id = p.player_id
    {where_clause}
    {group_by_clause}
    {order_by_clause};
"""

    try:
        conn = psycopg2.connect(host=SERVER, user=USERNAME, password=PASSWORD, dbname=DATABASE)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if query_params:
            cursor.execute(sql_query, query_params)
        else:
            cursor.execute(sql_query)
            
        results = cursor.fetchall()
        conn.close()

        # --- Reformat Data for Frontend Graph ---
        formatted_dict = {}
        
        # Force the metric key to lowercase so React/Recharts can always find the data
        metric_key = 'totalPoints' if request.score.lower() == 'total' else request.score.lower()
        
        # Force cumulative tracking for wins, regardless of what handler the frontend asks for
        is_cumulative = request.handler.lower() == 'cumulative' or request.score.lower() == 'wins'
        running_totals = {}
        
        for row in results:
            interval = row['time_interval']
            
            if interval not in formatted_dict:
                formatted_dict[interval] = {
                    "date": str(interval),
                    "winner": None,
                    "_max_score": -float('inf'), 
                    "results": []
                }
            
            score = row['calculated_score'] if row['calculated_score'] is not None else 0
            player_name = row['name'] 
            
            # Apply cumulative math 
            if is_cumulative:
                running_totals[player_name] = running_totals.get(player_name, 0) + score
                display_score = running_totals[player_name]
            else:
                display_score = score
            
            # Append the calculated display_score
            formatted_dict[interval]["results"].append({
                "player": player_name,
                metric_key: display_score
            })
            
            # Evaluate the winner based on the display score
            if display_score > formatted_dict[interval]["_max_score"]:
                formatted_dict[interval]["_max_score"] = display_score
                formatted_dict[interval]["winner"] = player_name
                
        final_output = []
        
        for index, (_, data) in enumerate(formatted_dict.items(), start=1):
            del data["_max_score"]
            final_output.append({
                "id": index,
                **data
            })

        return final_output
   
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))