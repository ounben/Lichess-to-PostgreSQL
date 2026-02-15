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

def update_metrics_full():
    try:
        with psycopg.connect(DB_CONFIG) as conn:
            with conn.cursor() as cur:

                # cur.execute("SELECT batch_id FROM metrics WHERE url IS NULL;")
                # rows = cur.fetchall()
                cur.execute("SELECT batch_id FROM metrics WHERE url IS NULL ORDER BY time DESC LIMIT 1000;")
                rows = cur.fetchall()
                
                for row in rows:
                    batch_id = row[0]

                    # 
                    if not batch_id or str(batch_id).strip() == "":
                        continue

                    url_api = f"https://lichess.org/api/game/{batch_id}"
                    
                    try:
                        response = requests.get(url_api, headers=HEADERS, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            
                            clock = data.get("clock", {})
                            players = data.get("players", {})
                            white = players.get("white", {})
                            black = players.get("black", {})

                            params = (
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
                                white.get("userId"),
                                white.get("rating"),
                                white.get("ratingDiff"),  
                                black.get("userId"),
                                black.get("rating"),
                                black.get("ratingDiff"),
                                data.get("winner"),
                                data.get("url"),
                                batch_id
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
                                    url = %s
                                WHERE batch_id = %s
                            """, params)
                            
                            conn.commit()
                            print(f"Update abgeschlossen: {batch_id}")

                        elif response.status_code == 429:
                            print("Rate Limit erreicht. Pause 60s.")
                            time.sleep(120)
                        
                        elif response.status_code == 404:
                            print(f"Game {batch_id} existiert nicht (404).")
                        
                            cur.execute("""
                                UPDATE metrics 
                                SET game_status = '404_NOT_FOUND',
                                    url = 'NOT_FOUND'
                                WHERE batch_id = %s
                            """, (batch_id,))
                        conn.commit()
                        # pause
                        # time.sleep(0.05)
                        time.sleep(1.0)

                    except Exception as e:
                        print(f"Fehler  Game {batch_id}: {e}")

    except Exception as e:
        print(f"Datenbankfehler: {e}")

if __name__ == "__main__":
    update_metrics_full()
