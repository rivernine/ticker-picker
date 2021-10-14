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