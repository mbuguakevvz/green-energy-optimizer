import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from prophet import Prophet
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

# --- Create forecast table ---
cur.execute("""
    CREATE TABLE IF NOT EXISTS energy_demand_forecast (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(10),
        country_name VARCHAR(100),
        forecast_date DATE,
        predicted_demand_index FLOAT,
        lower_bound FLOAT,
        upper_bound FLOAT,
        is_historical BOOLEAN,
        generated_at TIMESTAMP DEFAULT NOW()
    );
""")
conn.commit()

# --- Load climate data ---
df = pd.read_sql("""
    SELECT
        country_code,
        country_name,
        date,
        solar_irradiance_wm2,
        max_temp_c,
        precipitation_mm,
        wind_speed_ms
    FROM raw_climate
    ORDER BY country_code, date
""", conn)

df["date"] = pd.to_datetime(df["date"])

# --- Demand index formula ---
# Higher temp + lower rain + lower solar = higher energy demand
df["demand_index"] = (
    (df["max_temp_c"].fillna(df["max_temp_c"].mean()) * 1.5) +
    (100 - df["solar_irradiance_wm2"].fillna(0).clip(0, 100)) * 0.3 +
    (50 - df["precipitation_mm"].fillna(0).clip(0, 50)) * 0.2
)

countries = df["country_code"].unique()
cur.execute("TRUNCATE TABLE energy_demand_forecast;")

print("\n" + "="*60)
print("  ENERGY DEMAND FORECAST — East Africa 2022–2027")
print("="*60)

for code in countries:
    country_df = df[df["country_code"] == code].copy()
    country_name = country_df["country_name"].iloc[0]

    print(f"\n  Forecasting for {country_name}...")

    prophet_df = country_df[["date", "demand_index"]].rename(
        columns={"date": "ds", "demand_index": "y"}
    )

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.95
    )
    model.fit(prophet_df)

    # Forecast 2 years ahead
    future = model.make_future_dataframe(periods=730, freq="D")
    forecast = model.predict(future)

    inserted = 0
    for _, row in forecast.iterrows():
        is_historical = row["ds"] <= prophet_df["ds"].max()
        cur.execute("""
            INSERT INTO energy_demand_forecast (
                country_code, country_name, forecast_date,
                predicted_demand_index, lower_bound, upper_bound,
                is_historical
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            code,
            country_name,
            row["ds"].date(),
            round(float(row["yhat"]), 4),
            round(float(row["yhat_lower"]), 4),
            round(float(row["yhat_upper"]), 4),
            bool(is_historical)
        ))
        inserted += 1

    conn.commit()
    print(f"  Inserted {inserted} forecast records for {country_name}")

cur.close()
conn.close()
print(f"\nDone. Forecasts saved for {len(countries)} countries through 2027.")