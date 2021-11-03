from sqlalchemy import create_engine
import pymysql
import pandas as pd
from pykrx import stock
import time
from datetime import datetime, timedelta

ADDR = '192.168.56.100'
PORT = '3306'
DB = 'INDEX_DUCK'
ID = 'root'
PW = 'root'

db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()

### 1. 종목 최신화
print(">> 1. 시가총액 5천억 이상 ticker 최신화")

# 1.0. 티커 조회
print("1.0. 티커 조회")
cursor.execute("SELECT DISTINCT ticker FROM stocks_price")
tickers = list(map(lambda x: x[0], cursor.fetchall()))

# 1.1. 업데이트 기간 설정
print("1.1. 업데이트 기간 설정")
date = str(datetime.now().date()).replace('-', '')
print("기간: (%s)" %(date))

# 1.2. 기존 데이터 제거
print("1.2. 기존 데이터 제거 (%s)" %(date))
cursor.execute("DELETE FROM stocks_price WHERE date = " + date)
db.commit()
db.close()

# 1.3. 새로운 데이터 업데이트
print("1.3. 새로운 데이터 업데이트 (%s)" %(date))
for ticker in tickers:
  try:
    df = stock.get_market_ohlcv_by_date(str(datetime.now().date() - timedelta(days=1)).replace('-', ''), date, ticker)
    time.sleep(0.1)
    df['ticker'] = ticker
    df = df.rename(columns={'티커':'ticker', '시가':'open', '고가':'high', '저가':'low', '종가':'close', '거래량':'volume'})    
    df.index.names = ['date']
    df = df[['ticker', 'open', 'high', 'low', 'close', 'volume']]

    db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
    conn = db_connection.connect()
    df.to_sql(name='stocks_price', con=db_connection, if_exists='append', index=True, index_label="date")
    conn.close()
  except Exception as ex:
    print(ex, ticker)
    pass