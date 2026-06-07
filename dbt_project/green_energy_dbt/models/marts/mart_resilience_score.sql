with energy as (
    select
        country_code,
        country_name,
        year,
        electricity_access_pct,
        poverty_rate,
        population,
        gdp_per_capita
    from {{ ref('stg_energy_access') }}
),

climate as (
    select
        country_code,
        year,
        avg(avg_solar_irradiance)   as annual_avg_solar,
        avg(avg_max_temp_c)         as annual_avg_temp,
        sum(total_precipitation_mm) as annual_precipitation,
        avg(avg_wind_speed_ms)      as annual_avg_wind
    from {{ ref('stg_climate_risk') }}
    group by country_code, year
),

displacement as (
    select
        country_code,
        year,
        total_displaced,
        displacement_rate_pct
    from {{ ref('stg_displacement') }}
),

joined as (
    select
        e.country_code,
        e.country_name,
        e.year,
        e.electricity_access_pct,
        e.poverty_rate,
        e.population,
        e.gdp_per_capita,
        c.annual_avg_solar,
        c.annual_avg_temp,
        c.annual_precipitation,
        c.annual_avg_wind,
        d.total_displaced,
        d.displacement_rate_pct
    from energy e
    left join climate c
        on e.country_code = c.country_code and e.year = c.year
    left join displacement d
        on e.country_code = d.country_code and e.year = d.year
),

scored as (
    select
        *,
        -- Energy vulnerability: lower access = higher vulnerability (0-100)
        round(cast(100 - coalesce(electricity_access_pct, 0) as numeric), 2)
            as energy_vulnerability_score,

        -- Climate stress: higher temp + lower rainfall = more stress (0-100)
        round(cast(
            least(100, greatest(0,
                (coalesce(annual_avg_temp, 25) - 20) * 3 +
                (500 - least(coalesce(annual_precipitation, 500), 500)) / 10
            ))
        as numeric), 2) as climate_stress_score,

        -- Displacement pressure: based on displacement rate (0-100)
        round(cast(
            least(100, coalesce(displacement_rate_pct, 0) * 10)
        as numeric), 2) as displacement_pressure_score,

        -- Solar opportunity: higher irradiance = better solar potential (0-100)
        round(cast(
            least(100, coalesce(annual_avg_solar, 0) / 3)
        as numeric), 2) as solar_opportunity_score

    from joined
),

final as (
    select
        *,
        -- Composite resilience score (lower = more vulnerable = higher priority)
        round(cast(
            (energy_vulnerability_score * 0.40) +
            (climate_stress_score       * 0.30) +
            (displacement_pressure_score * 0.20) +
            ((100 - solar_opportunity_score) * 0.10)
        as numeric), 2) as resilience_priority_score
    from scored
)

select * from final
order by resilience_priority_score desc