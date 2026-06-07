with latest as (
    select
        country_code,
        country_name,
        max(year) as latest_year
    from {{ ref('mart_resilience_score') }}
    group by country_code, country_name
),

latest_scores as (
    select
        r.*,
        l.latest_year
    from {{ ref('mart_resilience_score') }} r
    inner join latest l
        on r.country_code = l.country_code
        and r.year = l.latest_year
),

ranked as (
    select
        country_code,
        country_name,
        year,
        electricity_access_pct,
        poverty_rate,
        population,
        gdp_per_capita,
        annual_avg_solar,
        annual_avg_temp,
        annual_precipitation,
        total_displaced,
        displacement_rate_pct,
        energy_vulnerability_score,
        climate_stress_score,
        displacement_pressure_score,
        solar_opportunity_score,
        resilience_priority_score,
        rank() over (
            order by resilience_priority_score desc
        ) as deployment_priority_rank,
        case
            when resilience_priority_score >= 70 then 'CRITICAL'
            when resilience_priority_score >= 50 then 'HIGH'
            when resilience_priority_score >= 30 then 'MEDIUM'
            else 'LOW'
        end as priority_tier
    from latest_scores
)

select * from ranked
order by deployment_priority_rank