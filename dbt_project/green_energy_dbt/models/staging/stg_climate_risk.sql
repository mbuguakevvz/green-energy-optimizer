with source as (
    select
        country_code,
        country_name,
        city,
        date,
        solar_irradiance_wm2,
        max_temp_c,
        precipitation_mm,
        wind_speed_ms
    from raw_climate
),

aggregated as (
    select
        country_code,
        country_name,
        extract(year from date)  as year,
        extract(month from date) as month,
        round(cast(avg(solar_irradiance_wm2) as numeric), 2) as avg_solar_irradiance,
        round(cast(avg(max_temp_c) as numeric), 2)           as avg_max_temp_c,
        round(cast(sum(precipitation_mm) as numeric), 2)     as total_precipitation_mm,
        round(cast(avg(wind_speed_ms) as numeric), 2)        as avg_wind_speed_ms,
        count(*) as days_recorded
    from source
    group by country_code, country_name, year, month
)

select * from aggregated