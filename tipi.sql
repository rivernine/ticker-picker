-- Create Table 
CREATE TABLE boll  (
  date    date,
  ticker  varchar(10),
  name    varchar(255),
  close   bigint,
  low     bigint,
  medium  bigint,
  high    bigint,
  primary key (ticker, date)
) engine = InnoDB;

-- Pick
SELECT T12.*, boll.close, boll.low, boll.medium, boll.high
FROM (
  SELECT T1.*, T2.period, T2.indVolCum, T2.insVolCum, T2.forVolCum
  FROM (
    SELECT ticker, name, market, cap, per, pbr
    FROM stocks_info
    WHERE cap >= 100000000000
    AND per >= 1
    AND per <= 20
  ) AS T1
  JOIN (
    SELECT *
    FROM correl
    -- WHERE forVolCum >= 0.9
    WHERE period = 'last_3m'
  ) AS T2
  ON(T1.ticker = T2.ticker)
) AS T12
JOIN boll
ON (T12.ticker = boll.ticker)
WHERE boll.close < boll.low
LIMIT 10;