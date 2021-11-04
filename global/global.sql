CREATE TABLE mfi (
  date      date,
  symbol    varchar(50),
  tp        double,
  mfi       double,
  mfi_diff  double,
  primary key (symbol, date)
) engine = InnoDB;

CREATE TABLE boll  (
  date      date,
  symbol    varchar(50),
  close     double,
  low       double,
  medium    double,
  high      double,
  bandWidth double,
  position  double,
  primary key (symbol, date)
) engine = InnoDB;

CREATE TABLE stocks_price (
  date    date,
  symbol  varchar(50),
  open    double,
  high    double,
  low     double,
  close   double,
  volume  bigint,
  primary key (symbol, date)
) engine = InnoDB;