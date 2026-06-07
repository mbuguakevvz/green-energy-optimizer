# ⚡ Green Energy Access & Resilience Optimizer
### East Africa Energy Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.10-blue)
![dbt](https://img.shields.io/badge/dbt-1.8.0-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Live-red)
![License](https://img.shields.io/badge/License-MIT-green)

An end-to-end data engineering pipeline that identifies where solar microgrid
deployment will save the most lives per dollar invested across East Africa —
combining real-time energy access, climate risk, and displacement data into
an actionable resilience scoring engine.

---

## 🌍 Problem Statement

Over **600 million people** in Sub-Saharan Africa lack access to electricity.
Health clinics lose vaccine cold chains. Water pumps fail. Climate shocks knock
out the diesel generators that vulnerable communities depend on. Solar microgrids
are the proven solution — but deployment decisions are made without data.

This platform changes that by giving NGOs, governments, and climate finance
institutions a **data-driven map of where energy intervention saves the most
lives**.

---

## 🎯 Target Countries

| Country | Population | Electricity Access | Displaced Persons |
|---|---|---|---|
| Kenya | 55M | 76.2% | 833,704 |
| Uganda | 48M | 51.5% | 1,806,881 |
| Tanzania | 65M | 48.3% | N/A |
| Ethiopia | 126M | 55.4% | 3,344,414 |
| Rwanda | 14M | 63.9% | 143,061 |
| Somalia | 18M | <30% | 3,900,000+ |

---

## 🏗️ Architecture---

## 📊 Data Sources

| Source | Data | Records |
|---|---|---|
| World Bank API | Electrification rate, poverty, population, GDP | 215 |
| Open-Meteo API | Solar irradiance, temperature, precipitation, wind | 9,702 |
| UNHCR API | Refugees, IDPs, asylum seekers, stateless persons | 75 |
| Prophet Forecasts | Energy demand index through 2027 | 14,082 |

---

## 🧠 Resilience Scoring Methodology

Each country receives a **Resilience Priority Score (0–100)** — higher means
more urgent intervention needed:| Component | Description |
|---|---|
| Energy Vulnerability | Inverse of electricity access percentage |
| Climate Stress | Heat exposure + drought risk index |
| Displacement Pressure | Displaced population as % of total |
| Solar Deficit | Inverse of solar irradiance potential |

**Priority Tiers:**
- 🔴 CRITICAL (≥70) — Immediate intervention required
- 🟠 HIGH (≥50) — Accelerated deployment needed
- 🟢 MEDIUM (≥30) — Planned expansion advised
- 🔵 LOW (<30) — Optimization of existing infrastructure

---

## 📁 Project Structure---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/mbuguakevvz/green-energy-optimizer.git
cd green-energy-optimizer

# Create virtual environment
python -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Running the Pipeline

```bash
# Run full pipeline
python orchestration/pipeline.py

# Or run individual stages
python ingestion/fetch_worldbank.py
python ingestion/fetch_openmeteo.py
python ingestion/fetch_unhcr.py

# dbt transformations
cd dbt_project/green_energy_dbt
dbt run
dbt test

# Scoring + forecasting
python optimization/recommender.py
python forecasting/demand_forecast.py

# Launch dashboard
streamlit run dashboard/app.py
```

---

## 🌱 Humanitarian Impact

This platform directly supports:

- **SDG 7** — Affordable and Clean Energy
- **SDG 13** — Climate Action
- **SDG 1** — No Poverty
- **SDG 10** — Reduced Inequalities

Target users include UNHCR, UNDP, GIZ, Practical Action, SNV Netherlands,
and national energy ministries across East Africa.

---

## 👤 Author

**Kevin Mbugua**
Data Engineer | NGO & Humanitarian Data Specialist
📍 Nairobi, Kenya
🔗 [github.com/mbuguakevvz](https://github.com/mbuguakevvz)

---

## 📄 License

MIT License — free to use, adapt, and build upon.