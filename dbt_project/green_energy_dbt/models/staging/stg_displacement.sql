with source as (
    select
        country_code,
        country_name,
        year,
        refugees,
        asylum_seekers,
        idps,
        stateless,
        total_displaced
    from raw_displacement
)

select
    country_code,
    country_name,
    year,
    refugees,
    asylum_seekers,
    idps,
    stateless,
    total_displaced,
   round(
        (cast(total_displaced as numeric) /
        nullif(
            (select value from raw_worldbank w
             where w.country_code = source.country_code
               and w.year = source.year
               and w.indicator_code = 'SP.POP.TOTL'
             limit 1), 0
        ) * 100)::numeric, 4
    ) as displacement_rate_pct
from source