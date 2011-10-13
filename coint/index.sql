select 
    F16_1090 as code
    ,ob_object_name_1090 as name
    ,F4_1120 as preclose
    ,F5_1120 as open
    ,F6_1120 as high
    ,F7_1120 as low
    ,F2_1120 as "DATE"
    ,F9_1120 as vol
    ,F11_1120 as turnover
    --,TO_CHAR(1000*F9_1120/F11_1120, 'FM9999.99') as avgprice
from wind.tb_object_1090,wind.TB_OBJECT_1120
where
    --F16_1090='000909' --300����
    --F16_1090='000913' --300ҽҩ
    --F16_1090='000912' --300����
    --F16_1090='000951' --300����
    --F16_1090='000914' --300����
    --F16_1090='000910' --300��ҵ
    F16_1090='000916' --300����
    and F1_1120=F2_1090
    and F4_1090='S'-- and F2_1120='20110915'
    and F4_1120 is not NULL
order by "DATE"