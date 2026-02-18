import psycopg
import requests
import time
# pip install "psycopg[binary]"

DB_CONFIG = "host=postgres_db dbname=fishnet_stats user=fish_admin password=passwort"
LICHESS_TOKEN = "lip_bK..."
HEADERS = {
    "Authorization": f"Bearer {LICHESS_TOKEN}",
    "Accept": "application/json"    
}

QUERY_PARAMS = {
    "moves": "false",
    "clocks": "false",
    "evals": "false",
    "accuracy": "true",
    "division": "false"
}

def update_metrics_full():
    try:
        with psycopg.connect(DB_CONFIG) as conn:
            with conn.cursor() as cur:

                cur.execute("SELECT batch_id FROM metrics WHERE opening_eco IS NULL ORDER BY time DESC LIMIT 1000;")
                rows = cur.fetchall()
                
                for row in rows:
                    batch_id = row[0]

                    if not batch_id or str(batch_id).strip() == "":
                        continue

                    url_api = f"https://lichess.org/game/export/{batch_id}"
                    
                    try:
                        response = requests.get(url_api, headers=HEADERS, params=QUERY_PARAMS, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                         
                            clock = data.get("clock", {})
                            players = data.get("players", {})
                            white = players.get("white", {})
                            black = players.get("black", {})
                            white_user = white.get("user", {})
                            black_user = black.get("user", {})
                            white_analysis = white.get("analysis", {})
                            black_analysis = black.get("analysis", {})
                            opening = data.get("opening", {})

                            db_params = (
                                data.get("rated"),
                                data.get("variant"),        #game_variant
                                data.get("speed"),
                                data.get("perf"),
                                data.get("createdAt"),     # game_created_at
                                data.get("lastMoveAt"),    # Keine SI-Konvertierung
                                data.get("turns"),
                                data.get("color"),
                                data.get("status"),         #game_status
                                clock.get("initial"),
                                clock.get("increment"),
                                clock.get("totalTime"),                                
                                white_user.get("id"),
                                white.get("rating"),
                                white.get("ratingDiff"),  # 
                                black_user.get("id"),
                                black.get("rating"),
                                black.get("ratingDiff"),
                                data.get("winner"),
                                data.get("url"),
                                white_analysis.get("inaccuracy"),
                                white_analysis.get("mistake"),
                                white_analysis.get("blunder"),
                                white_analysis.get("acpl"),
                                white_analysis.get("accuracy"),
                                black_analysis.get("inaccuracy"),
                                black_analysis.get("mistake"),
                                black_analysis.get("blunder"),
                                black_analysis.get("acpl"),
                                black_analysis.get("accuracy"),
                                opening.get("eco"),
                                opening.get("name"),
                                batch_id # 
                            )

                            cur.execute("""
                                UPDATE metrics 
                                SET rated = %s,
                                    game_variant = %s,
                                    speed = %s,
                                    perf = %s,
                                    game_created_at = to_timestamp(%s / 1000.0), -- entspricht created_at im JSON
                                    last_move_at = to_timestamp(%s / 1000.0),
                                    turns = %s,
                                    color = %s,
                                    game_status = %s,
                                    clock_initial = %s,
                                    clock_increment = %s,
                                    clock_total_time = %s,
                                    white_user_id = %s,
                                    white_rating = %s,
                                    white_rating_diff = %s,
                                    black_user_id = %s,
                                    black_rating = %s,
                                    black_rating_diff = %s,
                                    winner = %s,
                                    url = %s,
                                    white_inaccuracy = %s,
                                    white_mistake = %s,
                                    white_blunder = %s,
                                    white_acpl = %s,
                                    white_accuracy = %s,
                                    black_inaccuracy = %s,
                                    black_mistake = %s,
                                    black_blunder = %s,
                                    black_acpl = %s,
                                    black_accuracy = %s,
                                    opening_eco = %s,
                                    opening_name = %s
                                WHERE batch_id = %s
                            """, db_params)
                            
                            conn.commit()
                            print(f" Update (a): {batch_id} ")

                        elif response.status_code == 429:
                            print("Rate Limit erreicht. Pause 60s.")
                            time.sleep(60)
                        
                        elif response.status_code == 404:
                            print(f"Game {batch_id} existiert nicht (404). Markiere in DB.")
                        
                            cur.execute("""
                                UPDATE metrics 
                                SET game_status = '404_NOT_FOUND',
                                    url = 'NOT_FOUND'
                                WHERE batch_id = %s
                            """, (batch_id,))
                        conn.commit()
                        # time.sleep(0.05)
                        time.sleep(0.2)

                    except Exception as e:
                        print(f"Fehler bei Game {batch_id}: {e}")

    except Exception as e:
        print(f"Datenbankfehler: {e}")

if __name__ == "__main__":
    update_metrics_full()
