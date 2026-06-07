import requests
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# --- DB Connection ---
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
    CREATE TABLE IF NOT EXISTS raw_worldbank (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(10),
        country_name VARCHAR(100),
        indicator_code VARCHAR(100),
        indicator_name VARCHAR(255),
        year INTEGER,
        value FLOAT,
        ingested_at TIMESTAMP DEFAULT NOW()
    );
""")
conn.commit()

# --- Countries & Indicators ---
COUNTRIES = {
    "KE": "Kenya",
    "UG": "Uganda",
    "TZ": "Tanzania",
    "ET": "Ethiopia",
    "RW": "Rwanda",
    "SO": "Somalia"
}

INDICATORS = {
    "EG.ELC.ACCS.ZS": "Access to electricity (% of population)",
    "SI.POV.DDAY":     "Poverty headcount ratio at $2.15/day (%)",
    "SP.POP.TOTL":     "Population total",
    "NY.GDP.PCAP.CD":  "GDP per capita (current US$)"
}

BASE_URL = "https://api.worldbank.org/v2/country/{}/indicator/{}?format=json&mrv=10&per_page=10"

# --- Fetch & Insert ---
total_inserted = 0

for code, name in COUNTRIES.items():
    for indicator_code, indicator_name in INDICATORS.items():
        url = BASE_URL.format(code, indicator_code)
        print(f"Fetching {indicator_name} for {name}...")

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if len(data) < 2 or not data[1]:
                print(f"  No data returned for {name} - {indicator_code}")
                continue

            records = data[1]
            inserted = 0

            for record in records:
                if record.get("value") is None:
                    continue

                cur.execute("""
                    INSERT INTO raw_worldbank
                        (country_code, country_name, indicator_code, indicator_name, year, value)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    code,
                    name,
                    indicator_code,
                    indicator_name,
                    int(record["date"]),
                    float(record["value"])
                ))
                inserted += 1

            conn.commit()
            total_inserted += inserted
            print(f"  Inserted {inserted} records for {name}")

        except Exception as e:
            print(f"  ERROR for {name} - {indicator_code}: {e}")

cur.close()
conn.close()
print(f"\nDone. Total records inserted: {total_inserted}")