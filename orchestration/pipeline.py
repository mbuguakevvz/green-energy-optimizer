import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

steps = [
    ("World Bank Ingestion",    ["python", "ingestion/fetch_worldbank.py"]),
    ("Open-Meteo Ingestion",    ["python", "ingestion/fetch_openmeteo.py"]),
    ("UNHCR Ingestion",         ["python", "ingestion/fetch_unhcr.py"]),
    ("dbt Run",                 ["dbt", "run"],          "dbt_project/green_energy_dbt"),
    ("dbt Test",                ["dbt", "test"],         "dbt_project/green_energy_dbt"),
    ("Resilience Scoring",      ["python", "optimization/recommender.py"]),
    ("Demand Forecasting",      ["python", "forecasting/demand_forecast.py"]),
]

print("\n" + "="*60)
print("  GREEN ENERGY OPTIMIZER — Full Pipeline Run")
print("="*60)

for step in steps:
    name    = step[0]
    cmd     = step[1]
    workdir = step[2] if len(step) > 2 else None

    print(f"\n▶ Running: {name}...")
    result = subprocess.run(cmd, cwd=workdir)

    if result.returncode != 0:
        print(f"✗ FAILED: {name}")
        sys.exit(1)
    else:
        print(f"✓ DONE: {name}")

print("\n" + "="*60)
print("  Pipeline completed successfully.")
print("="*60)