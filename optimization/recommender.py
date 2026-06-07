import psycopg2
import os
import json
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

# --- Create output table ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS deployment_recommendations (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(10),
        country_name VARCHAR(100),
        year INTEGER,
        electricity_access_pct FLOAT,
        poverty_rate FLOAT,
        population FLOAT,
        gdp_per_capita FLOAT,
        annual_avg_solar FLOAT,
        annual_avg_temp FLOAT,
        annual_precipitation FLOAT,
        total_displaced BIGINT,
        displacement_rate_pct FLOAT,
        energy_vulnerability_score FLOAT,
        climate_stress_score FLOAT,
        displacement_pressure_score FLOAT,
        solar_opportunity_score FLOAT,
        resilience_priority_score FLOAT,
        deployment_priority_rank INTEGER,
        priority_tier VARCHAR(20),
        recommendation TEXT,
        generated_at TIMESTAMP DEFAULT NOW()
    );
""")
conn.commit()

# --- Fetch mart data ---
cur.execute("""
    SELECT
        dt.country_code,
        dt.country_name,
        dt.year,
        -- Pull best available electricity access (most recent non-null year)
        COALESCE(dt.electricity_access_pct, ea.electricity_access_pct) as electricity_access_pct,
        COALESCE(dt.poverty_rate, ea.poverty_rate)                     as poverty_rate,
        COALESCE(dt.population, ea.population)                         as population,
        COALESCE(dt.gdp_per_capita, ea.gdp_per_capita)                 as gdp_per_capita,
        dt.annual_avg_solar,
        dt.annual_avg_temp,
        dt.annual_precipitation,
        dt.total_displaced,
        dt.displacement_rate_pct,
        dt.energy_vulnerability_score,
        dt.climate_stress_score,
        dt.displacement_pressure_score,
        dt.solar_opportunity_score,
        dt.resilience_priority_score,
        dt.deployment_priority_rank,
        dt.priority_tier
    FROM mart_deployment_targets dt
    LEFT JOIN (
        SELECT country_code, electricity_access_pct, poverty_rate, population, gdp_per_capita
        FROM mart_resilience_score
        WHERE electricity_access_pct IS NOT NULL
        AND year = (
            SELECT max(year) FROM mart_resilience_score r2
            WHERE r2.country_code = mart_resilience_score.country_code
            AND r2.electricity_access_pct IS NOT NULL
        )
    ) ea ON dt.country_code = ea.country_code
    ORDER BY dt.deployment_priority_rank
""")

rows = cur.fetchall()
columns = [desc[0] for desc in cur.description]
records = [dict(zip(columns, row)) for row in rows]

def generate_recommendation(r):
    lines = []

    tier = r.get("priority_tier", "UNKNOWN")
    solar = r.get("annual_avg_solar") or 0
    access = r.get("electricity_access_pct") or 0
    displaced = r.get("total_displaced") or 0
    poverty = r.get("poverty_rate") or 0
    temp = r.get("annual_avg_temp") or 0

    if tier == "CRITICAL":
        lines.append("URGENT: Immediate solar microgrid deployment recommended.")
    elif tier == "HIGH":
        lines.append("HIGH PRIORITY: Accelerated energy access intervention needed.")
    elif tier == "MEDIUM":
        lines.append("MEDIUM PRIORITY: Planned energy access expansion advised.")
    else:
        lines.append("LOWER PRIORITY: Maintenance and optimization of existing infrastructure.")

    if solar > 200:
        lines.append(f"Strong solar potential ({solar:.1f} W/m²) — ideal for photovoltaic deployment.")
    elif solar > 150:
        lines.append(f"Moderate solar potential ({solar:.1f} W/m²) — solar viable with proper siting.")
    else:
        lines.append(f"Lower solar irradiance ({solar:.1f} W/m²) — consider hybrid wind-solar systems.")

    if access < 30:
        lines.append(f"Critical electricity gap: only {access:.1f}% population has access.")
    elif access < 60:
        lines.append(f"Significant electricity gap: {access:.1f}% population has access.")
    else:
        lines.append(f"Moderate electricity coverage: {access:.1f}% population has access.")

    if displaced > 500000:
        lines.append(f"Large displaced population ({displaced:,}) — prioritize refugee camp microgrids.")
    elif displaced > 100000:
        lines.append(f"Significant displaced population ({displaced:,}) — include displacement camps in planning.")

    if poverty and poverty > 40:
        lines.append(f"High poverty rate ({poverty:.1f}%) — subsidized energy tariffs essential.")

    if temp > 30:
        lines.append(f"High heat stress ({temp:.1f}°C avg) — cooling energy demand will be critical.")

    return " ".join(lines)

# --- Insert recommendations ---
print("\n" + "="*65)
print("  GREEN ENERGY ACCESS & RESILIENCE OPTIMIZER")
print("  East Africa Deployment Recommendations")
print("="*65)

cur.execute("TRUNCATE TABLE deployment_recommendations;")

for r in records:
    recommendation = generate_recommendation(r)

    cur.execute("""
        INSERT INTO deployment_recommendations (
            country_code, country_name, year,
            electricity_access_pct, poverty_rate, population, gdp_per_capita,
            annual_avg_solar, annual_avg_temp, annual_precipitation,
            total_displaced, displacement_rate_pct,
            energy_vulnerability_score, climate_stress_score,
            displacement_pressure_score, solar_opportunity_score,
            resilience_priority_score, deployment_priority_rank,
            priority_tier, recommendation
        ) VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
    """, (
        r["country_code"], r["country_name"], r["year"],
        r["electricity_access_pct"], r["poverty_rate"],
        r["population"], r["gdp_per_capita"],
        r["annual_avg_solar"], r["annual_avg_temp"], r["annual_precipitation"],
        r["total_displaced"], r["displacement_rate_pct"],
        r["energy_vulnerability_score"], r["climate_stress_score"],
        r["displacement_pressure_score"], r["solar_opportunity_score"],
        r["resilience_priority_score"], r["deployment_priority_rank"],
        r["priority_tier"], recommendation
    ))

    print(f"\n  #{r['deployment_priority_rank']} — {r['country_name']} [{r['priority_tier']}]")
    print(f"  Resilience Priority Score : {r['resilience_priority_score']}")
    print(f"  Electricity Access        : {r['electricity_access_pct']}%")
    print(f"  Solar Irradiance          : {r['annual_avg_solar']} W/m²")
    print(f"  Total Displaced           : {r['total_displaced']:,}" if r['total_displaced'] else "  Total Displaced           : N/A")
    print(f"  Recommendation: {recommendation}")
    print("-"*65)

conn.commit()
cur.close()
conn.close()
print(f"\nDone. {len(records)} country recommendations saved to database.")