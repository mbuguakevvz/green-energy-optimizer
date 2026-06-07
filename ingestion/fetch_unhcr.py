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
    CREATE TABLE IF NOT EXISTS raw_displacement (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(10),
        country_name VARCHAR(100),
        year INTEGER,
        refugees BIGINT,
        asylum_seekers BIGINT,
        idps BIGINT,
        stateless BIGINT,
        total_displaced BIGINT,
        ingested_at TIMESTAMP DEFAULT NOW()
    );
""")
conn.commit()

COUNTRIES = [
    {"code": "KE",  "iso3": "KEN", "name": "Kenya"},
    {"code": "UG",  "iso3": "UGA", "name": "Uganda"},
    {"code": "TZ",  "iso3": "TZA", "name": "Tanzania"},
    {"code": "ET",  "iso3": "ETH", "name": "Ethiopia"},
    {"code": "RW",  "iso3": "RWA", "name": "Rwanda"},
    {"code": "SO",  "iso3": "SOM", "name": "Somalia"},
]

BASE_URL = "https://api.unhcr.org/population/v1/population/?limit=100&yearFrom=2010&yearTo=2024&coa={iso3}"

total_inserted = 0

for country in COUNTRIES:
    url = BASE_URL.format(iso3=country["iso3"])
    print(f"Fetching displacement data for {country['name']}...")
    print(f"  URL: {url}")

    try:
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=20)
        print(f"  Status code: {response.status_code}")

        data = response.json()
        print(f"  Keys in response: {list(data.keys())}")

        # Try multiple possible response structures
        items = (
            data.get("items") or
            data.get("data") or
            data.get("results") or
            data.get("population") or
            []
        )

        if not items:
            print(f"  Raw response preview: {str(data)[:300]}")
            print(f"  No displacement data found for {country['name']}")
            continue

        inserted = 0
        for item in items:
            refugees       = int(item.get("refugees") or 0)
            asylum_seekers = int(item.get("asylum_seekers") or 0)
            idps           = int(item.get("idps") or 0)
            stateless      = int(item.get("stateless") or 0)
            total          = refugees + asylum_seekers + idps + stateless
            cur.execute("""
                INSERT INTO raw_displacement
                    (country_code, country_name, year, refugees,
                     asylum_seekers, idps, stateless, total_displaced)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                country["code"],
                country["name"],
                item.get("year"),
                refugees,
                asylum_seekers,
                idps,
                stateless,
                total
            ))
            inserted += 1

        conn.commit()
        total_inserted += inserted
        print(f"  Inserted {inserted} records for {country['name']}")

    except Exception as e:
        print(f"  ERROR for {country['name']}: {e}")

cur.close()
conn.close()
print(f"\nDone. Total displacement records inserted: {total_inserted}")