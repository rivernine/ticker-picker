-- Create Table 
CREATE TABLE mfi (
  date      date,
  ticker    varchar(10),
  period    int,
  mfi double,
  z_score   double,
  primary key (ticker, date, period)
) engine = InnoDB;

CREATE TABLE z_score  (
  date      date,
  ticker    varchar(10),
  period    int,
  bandWidth double,
  z_score   double,
  primary key (ticker, date, period)
) engine = InnoDB;

CREATE TABLE boll  (
  date      date,
  ticker    varchar(10),
  close     bigint,
  low       bigint,
  medium    bigint,
  high      bigint,
  bandWidth double,
  primary key (ticker, date)
) engine = InnoDB;

CREATE TABLE stocks_price (
  date    date,
  ticker  varchar(10),
  open   bigint,
  high    bigint,
  low     bigint,
  close   bigint,
  volume  bigint,
  primary key (ticker, date)
) engine = InnoDB;

-- 최근 n일 간 볼린저밴드 조회
SELECT *
FROM boll
WHERE ticker = '005930'
AND date <= '20211018'
ORDER BY date DESC
LIMIT n;


-- 최근 20일 간 내역 조회
SELECT *
FROM stocks_price
WHERE ticker = '005930'
AND date <= '20211018'
ORDER BY date DESC
LIMIT 20;

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