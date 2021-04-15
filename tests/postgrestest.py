import datetime
import os

import psycopg2

DATABASE_URL = "postgres://ojgkovunswhndg:9936b33ab2efff9a5091943ee8c5a31deb0b2495770e62dee7eff1b9e50cc879@ec2-18-233" \
               "-83-165.compute-1.amazonaws.com:5432/d3l2d60pufekgb"  # os.environ.get('DATABASE_URL')

if __name__ == "__main__":
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO showtimes (showtime, \"cast\") VALUES (%(showtime)s, %(cast)s)",
                        {"showtime": datetime.datetime(2021, 5, 16, 18, 0), "cast": "Hakuna"})
            # cur.execute("DELETE FROM showtimes WHERE showtime=%(showtime)s",
            #             {"showtime": datetime.datetime(2021, 5, 15, 14, 0)})
            cur.execute("SELECT * FROM showtimes;")
            print(cur.fetchall())
