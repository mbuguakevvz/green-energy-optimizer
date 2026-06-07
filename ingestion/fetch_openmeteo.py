import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

# --- Create Table ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_climate (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(10),
        country_name VARCHAR(100),
        city VARCHAR(100),
        date DATE,
        solar_irradiance_wm2 FLOAT,
        max_temp_c FLOAT,
        precipitation_mm FLOAT,
        wind_speed_ms FLOAT,
        ingested_at TIMESTAMP DEFAULT NOW()
    );
""")
conn.commit()

# --- Country Capitals with Coordinates ---
LOCATIONS = [
    {"code": "KE", "name": "Kenya",    "city": "Nairobi",      "lat": -1.2921,  "lon": 36.8219},
    {"code": "UG", "name": "Uganda",   "city": "Kampala",      "lat":  0.3476,  "lon": 32.5825},
    {"code": "TZ", "name": "Tanzania", "city": "Dodoma",       "lat": -6.1731,  "lon": 35.7395},
    {"code": "ET", "name": "Ethiopia", "city": "Addis Ababa",  "lat":  9.0320,  "lon": 38.7469},
    {"code": "RW", "name": "Rwanda",   "city": "Kigali",       "lat": -1.9441,  "lon": 30.0619},
    {"code": "SO", "name": "Somalia",  "city": "Mogadishu",    "lat":  2.0469,  "lon": 45.3182},
]

BASE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude={lat}&longitude={lon}"
    "&start_date=2022-01-01&end_date=2026-06-05"
    "&daily=shortwave_radiation_sum,temperature_2m_max,precipitation_sum,wind_speed_10m_max"
    "&timezone=Africa%2FNairobi"
)

total_inserted = 0

for loc in LOCATIONS:
    url = BASE_URL.format(lat=loc["lat"], lon=loc["lon"])
    print(f"Fetching climate data for {loc['name']} ({loc['city']})...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        dates         = daily.get("time", [])
        solar         = daily.get("shortwave_radiation_sum", [])
        max_temp      = daily.get("temperature_2m_max", [])
        precipitation = daily.get("precipitation_sum", [])
        wind_speed    = daily.get("wind_speed_10m_max", [])

        inserted = 0
        for i, date in enumerate(dates):
            cur.execute("""
                INSERT INTO raw_climate
                    (country_code, country_name, city, date,
                     solar_irradiance_wm2, max_temp_c, precipitation_mm, wind_speed_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                loc["code"],
                loc["name"],
                loc["city"],
                date,
                solar[i]         if i < len(solar)         else None,
                max_temp[i]      if i < len(max_temp)      else None,
                precipitation[i] if i < len(precipitation) else None,
                wind_speed[i]    if i < len(wind_speed)    else None,
            ))
            inserted += 1

        conn.commit()
        total_inserted += inserted
        print(f"  Inserted {inserted} daily records for {loc['name']}")

    except Exception as e:
        print(f"  ERROR for {loc['name']}: {e}")

cur.close()
conn.close()
print(f"\nDone. Total climate records inserted: {total_inserted}")