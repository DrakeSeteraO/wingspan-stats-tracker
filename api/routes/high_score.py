from fastapi import APIRouter, HTTPException
from typing import List
import pymssql
import os
from dotenv import load_dotenv

from api.schema import HighScoreReturn

router = APIRouter()
load_dotenv()

SERVER = os.getenv('SERVER')
DATABASE = os.getenv('DATABASE')
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')

@router.get("/api/high-score", response_model=HighScoreReturn, response_model_exclude_none=True)
def get_high_scores():
    
    # 1. Personal Bests
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

    # 2. Global Records
    overall_query = """
        WITH UnpivotedStats AS (
            SELECT 
                CONVERT(varchar, a.date, 23) as date,
                c.name as achiever, Category, Score
            FROM game a
            JOIN player_game_stats b ON a.game_id = b.game_id
            JOIN player_info c ON b.player_id = c.player_id
            CROSS APPLY (
                VALUES 
                    ('Total Points', b.total), ('Bird Points', b.bird),
                    ('Bonus Cards', b.bonus_card), ('End of Round Goals', b.end_of_round_goals),
                    ('Eggs', b.eggs), ('Food on Cards', b.food_on_cards),
                    ('Tucked Cards', b.tucked_cards), ('Nectar', b.nectar)
            ) x (Category, Score)
            WHERE c.name != 'Unknown' AND Score IS NOT NULL
        ),
        PlayerScoreEarliest AS (
            SELECT 
                Category, Score, achiever, date,
                ROW_NUMBER() OVER(PARTITION BY Category, achiever, Score ORDER BY date ASC) as rn_player
            FROM UnpivotedStats
        ),
        RankedRecords AS (
            SELECT 
                Category as name, Score as score, achiever, date,
                RANK() OVER(PARTITION BY Category ORDER BY Score DESC) as rnk
            FROM PlayerScoreEarliest
            WHERE rn_player = 1
        )
        SELECT name, score, achiever, date FROM RankedRecords WHERE rnk = 1 ORDER BY name, date ASC;
    """

    # 3. NEW: Flock Superlatives
    superlatives_query = """
        -- 1. Heartbreak
        WITH Losers AS (
            SELECT c.name as achiever, b.total as score, CONVERT(varchar, a.date, 23) as date,
            ROW_NUMBER() OVER(ORDER BY b.total DESC, a.date ASC) as rn
            FROM game a JOIN player_game_stats b ON a.game_id = b.game_id JOIN player_info c ON b.player_id = c.player_id
            WHERE b.player_id != a.winner_id AND c.name != 'Unknown' AND b.total IS NOT NULL
        ),
        -- 2. Blowout & Skin of Their Beak (Shared CTE)
        RankedScores AS (
            -- We sort by total DESC, but if there's a tie, we force the actual winner into 1st place
            SELECT a.game_id, c.name, b.total, CONVERT(varchar, a.date, 23) as date,
            ROW_NUMBER() OVER(PARTITION BY a.game_id ORDER BY b.total DESC, CASE WHEN a.winner_id = b.player_id THEN 1 ELSE 2 END ASC) as place
            FROM game a JOIN player_game_stats b ON a.game_id = b.game_id JOIN player_info c ON b.player_id = c.player_id
            WHERE c.name != 'Unknown' AND b.total IS NOT NULL
        ),
        Margins AS (
            SELECT r1.name as achiever, (r1.total - r2.total) as margin, r1.date,
            ROW_NUMBER() OVER(ORDER BY (r1.total - r2.total) DESC, r1.date ASC) as rn
            FROM RankedScores r1 JOIN RankedScores r2 ON r1.game_id = r2.game_id AND r1.place = 1 AND r2.place = 2
        ),
        TightestWins AS (
            SELECT r1.name as achiever, r1.total as score, r1.date,
            ROW_NUMBER() OVER(ORDER BY r1.total DESC, r1.date ASC) as rn
            FROM RankedScores r1 JOIN RankedScores r2 ON r1.game_id = r2.game_id AND r1.place = 1 AND r2.place = 2
            WHERE r1.total = r2.total
        ),
        -- 3. Pacifist
        Winners AS (
            SELECT c.name as achiever, b.total as score, CONVERT(varchar, a.date, 23) as date,
            ROW_NUMBER() OVER(ORDER BY b.total ASC, a.date ASC) as rn
            FROM game a JOIN player_game_stats b ON a.game_id = b.game_id JOIN player_info c ON b.player_id = c.player_id
            WHERE b.player_id = a.winner_id AND c.name != 'Unknown' AND b.total > 0
        ),
        -- 4. Hyper-Specialist
        PlayerCategories AS (
            SELECT 
                a.game_id, c.name as achiever, b.total, CONVERT(varchar, a.date, 23) as date,
                cat.Category, cat.Score,
                ROW_NUMBER() OVER(PARTITION BY a.game_id, c.name ORDER BY cat.Score DESC) as cat_rn
            FROM game a 
            JOIN player_game_stats b ON a.game_id = b.game_id 
            JOIN player_info c ON b.player_id = c.player_id
            CROSS APPLY (
                VALUES 
                    ('Bird Points', b.bird), ('Bonus Cards', b.bonus_card),
                    ('End of Round Goals', b.end_of_round_goals), ('Eggs', b.eggs),
                    ('Food on Cards', b.food_on_cards), ('Tucked Cards', b.tucked_cards),
                    ('Nectar', b.nectar)
            ) cat (Category, Score)
            WHERE c.name != 'Unknown' AND b.total > 0
        ),
        Percentages AS (
            SELECT 
                achiever, CAST(ROUND((CAST(Score AS FLOAT) / total) * 100, 1) AS FLOAT) as pct, 
                Category, date,
                ROW_NUMBER() OVER(ORDER BY (CAST(Score AS FLOAT) / total) DESC, date ASC) as rn
            FROM PlayerCategories
            WHERE cat_rn = 1
        ),
        -- 5. All-Rounder (Lowest Variance)
        CategoryStats AS (
            SELECT a.game_id, c.name as achiever, CONVERT(varchar, a.date, 23) as date,
            CAST(b.bird AS FLOAT) as c1, CAST(b.bonus_card AS FLOAT) as c2, CAST(b.end_of_round_goals AS FLOAT) as c3,
            CAST(b.eggs AS FLOAT) as c4, CAST(b.food_on_cards AS FLOAT) as c5, CAST(b.tucked_cards AS FLOAT) as c6
            FROM game a JOIN player_game_stats b ON a.game_id = b.game_id JOIN player_info c ON b.player_id = c.player_id
            WHERE c.name != 'Unknown' AND b.total > 0
        ),
        Means AS (
            SELECT game_id, achiever, date, (c1+c2+c3+c4+c5+c6)/6.0 as mean, c1, c2, c3, c4, c5, c6 FROM CategoryStats
        ),
        Variances AS (
            SELECT achiever, date,
            (SQUARE(c1-mean) + SQUARE(c2-mean) + SQUARE(c3-mean) + SQUARE(c4-mean) + SQUARE(c5-mean) + SQUARE(c6-mean)) / 6.0 as variance,
            ROW_NUMBER() OVER(ORDER BY (SQUARE(c1-mean) + SQUARE(c2-mean) + SQUARE(c3-mean) + SQUARE(c4-mean) + SQUARE(c5-mean) + SQUARE(c6-mean)) / 6.0 ASC, date ASC) as rn
            FROM Means
        ),
        -- 6. Traditionalist
        Traditionalist AS (
            SELECT c.name as achiever, b.total as score, CONVERT(varchar, a.date, 23) as date,
            ROW_NUMBER() OVER(ORDER BY b.total DESC, a.date ASC) as rn
            FROM game a JOIN player_game_stats b ON a.game_id = b.game_id JOIN player_info c ON b.player_id = c.player_id
            WHERE c.name != 'Unknown' AND b.nectar = 0 AND b.total > 0
        ),
        -- 7. Egg Carton
        GameMinBirds AS (
            SELECT game_id, MIN(bird) as min_bird FROM player_game_stats GROUP BY game_id
        ),
        EggCarton AS (
            SELECT c.name as achiever, b.total as score, CONVERT(varchar, a.date, 23) as date,
            ROW_NUMBER() OVER(ORDER BY b.total DESC, a.date ASC) as rn
            FROM game a
            JOIN player_game_stats b ON a.game_id = b.game_id
            JOIN player_info c ON b.player_id = c.player_id
            JOIN GameMinBirds gmb ON a.game_id = gmb.game_id
            WHERE a.winner_id = b.player_id AND b.bird = gmb.min_bird AND c.name != 'Unknown' AND b.total > 0
        )

        -- Combine All
        SELECT 'The Heartbreak' as title, CAST(score AS VARCHAR) + ' pts' as value, achiever, date, 'Highest score that still lost the game.' as note FROM Losers WHERE rn = 1
        UNION ALL
        SELECT 'Biggest Blowout' as title, CAST(margin AS VARCHAR) + ' pt margin' as value, achiever, date, 'Largest point gap between 1st and 2nd place.' as note FROM Margins WHERE rn = 1
        UNION ALL
        SELECT 'Pacifist Victory' as title, CAST(score AS VARCHAR) + ' pts' as value, achiever, date, 'Lowest total score to successfully win a game.' as note FROM Winners WHERE rn = 1
        UNION ALL
        SELECT 'Hyper-Specialist' as title, CAST(pct AS VARCHAR) + '% of total' as value, achiever, date, 'Highest percentage of points from a single category (' + Category + ').' as note FROM Percentages WHERE rn = 1
        UNION ALL
        SELECT 'The All-Rounder' as title, CAST(CAST(ROUND(variance, 2) AS DECIMAL(10,2)) AS VARCHAR) as value, achiever, date, 'Most balanced scoring across all core categories (shown as statistical variance).' as note FROM Variances WHERE rn = 1
        UNION ALL
        SELECT 'Skin of Their Beak' as title, CAST(score AS VARCHAR) + ' pts' as value, achiever, date, 'Highest-scoring victory won by a food tiebreaker (0 pt margin).' as note FROM TightestWins WHERE rn = 1
        UNION ALL
        SELECT 'The Traditionalist' as title, CAST(score AS VARCHAR) + ' pts' as value, achiever, date, 'Highest winning score achieved with exactly 0 Nectar.' as note FROM Traditionalist WHERE rn = 1
        UNION ALL
        SELECT 'The Egg Carton' as title, CAST(score AS VARCHAR) + ' pts' as value, achiever, date, 'Highest-scoring victory achieved while having the lowest Bird Points at the table.' as note FROM EggCarton WHERE rn = 1;
    """
    
    try:
        conn = pymssql.connect(server=SERVER, user=USERNAME, password=PASSWORD, database=DATABASE)
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute(personal_query)
        personal_results = cursor.fetchall()
        
        cursor.execute(overall_query)
        overall_results = cursor.fetchall()

        cursor.execute(superlatives_query)
        superlative_results = cursor.fetchall()
        
        conn.close()
        
        # Group the overall records into the array structure
        grouped_overall = {}
        for row in overall_results:
            cat = row['name']
            if cat not in grouped_overall:
                grouped_overall[cat] = {"name": cat, "score": row['score'], "achievers": []}
            grouped_overall[cat]["achievers"].append({"name": row['achiever'], "date": row['date']})
            
        final_overall = list(grouped_overall.values())
        
        return {
            "personal": personal_results,
            "overall": final_overall,
            "superlatives": superlative_results # Append new list here
        }

    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))