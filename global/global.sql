CREATE TABLE mfi (
  date      date,
  symbol    varchar(50),
  period    int,
  tp        bigint,
  mfi       double,
  mfi_diff  double,
  primary key (symbol, date)
) engine = InnoDB;

CREATE TABLE boll  (
  date      date,
  symbol    varchar(50),
  close     bigint,
  low       bigint,
  medium    bigint,
  high      bigint,
  bandWidth double,
  position  double,
  primary key (symbol, date)
) engine = InnoDB;

CREATE TABLE stocks_price (
  date    date,
  symbol  varchar(50),
  open   bigint,
  high    bigint,
  low     bigint,
  close   bigint,
  volume  bigint,
  primary key (symbol, date)
) engine = InnoDB;