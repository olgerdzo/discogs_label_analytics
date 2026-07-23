drop materialized view if exists label_analytics_view;

create materialized view label_analytics_view as
select
    label_name,
    want,
    have,
    (want + have) as market_size,
    round((want::numeric / case when have = 0 then 1 else have end), 4) as want_to_have_ratio,
    round((want::numeric / case when have = 0 then 1 else have end) * log(10, case when want < 10 then 10 else want end), 4) as score_demand,
    round((want::numeric / case when have = 0 then 1 else have end) * log(10, case when have < 10 then 10 else have end), 4) as score_supply,
    round((want::numeric / case when have = 0 then 1 else have end) * log(10, case when (want + have) < 10 then 10 else (want + have) end), 4) as score
from label_data;
create unique index idx_label_analytics_name on label_analytics_view(label_name);