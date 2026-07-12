from fastapi import FastAPI, HTTPException
import pymssql
import os
import sys
from dotenv import load_dotenv

# Import your Pydantic model from the schema.py file in the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import StatsRequest

app = FastAPI()
load_dotenv()

# --- Azure SQL Configuration ---
SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

# Stack the root route to handle Vercel's file-based routing strip
@app.post("/api/trend")
@app.post("/")
def get_stats(request: StatsRequest):
    
    # Security Allowlists
    allowed_scores = {
        'total': 'total',
        'bird': 'bird',
        'bonus_card': 'bonus_card',
        'eggs': 'eggs',
        'food': 'food_on_cards',
        'tucked': 'tucked_cards',
        'nectar': 'nectar'
    }

    allowed_handlers = {
        'sum': 'SUM',
        'avg': 'AVG',
        'min': 'MIN',
        'max': 'MAX'
    }

    allowed_intervals = {
        'game': 'g.game_id',
        'day': 'CAST(g.date AS DATE)',
        'month': "FORMAT(g.date, 'yyyy-MM')",
        'year': "FORMAT(g.date, 'yyyy')",
        'all': "'All-Time'" # Wrapped in single quotes to act as a SQL string literal
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

    # Construct the Dynamic Query and Conditional WHERE Clause
    where_clause = ""
    query_params = ()

    if request.players:
        placeholders = ", ".join(["%s"] * len(request.players))
        where_clause = f"WHERE p.username IN ({placeholders})"
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
        FROM player_game_stats s
        JOIN game g ON s.game_id = g.game_id
        JOIN player_info p ON s.player_id = p.player_id
        {where_clause}
        {group_by_clause}
        {order_by_clause};
    """

    try:
        conn = pymssql.connect(
            server=SERVER,
            user=USERNAME,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = conn.cursor(as_dict=True)
        
        if query_params:
            cursor.execute(sql_query, query_params)
        else:
            cursor.execute(sql_query)
            
        results = cursor.fetchall()
        conn.close()

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