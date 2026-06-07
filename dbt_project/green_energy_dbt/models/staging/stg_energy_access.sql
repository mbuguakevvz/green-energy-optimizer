with source as (
    select
        country_code,
        country_name,
        indicator_code,
        indicator_name,
        year,
        value
    from raw_worldbank
    where indicator_code in (
        'EG.ELC.ACCS.ZS',
        'SI.POV.DDAY',
        'SP.POP.TOTL',
        'NY.GDP.PCAP.CD'
    )
),

pivoted as (
    select
        country_code,
        country_name,
        year,
        max(case when indicator_code = 'EG.ELC.ACCS.ZS' then value end) as electricity_access_pct,
        max(case when indicator_code = 'SI.POV.DDAY'    then value end) as poverty_rate,
        max(case when indicator_code = 'SP.POP.TOTL'    then value end) as population,
        max(case when indicator_code = 'NY.GDP.PCAP.CD' then value end) as gdp_per_capita
    from source
    group by country_code, country_name, year
)

select * from pivoted