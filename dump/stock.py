from sqlalchemy import create_engine
import pymysql
import pandas as pd
from pykrx import stock
import time
from datetime import datetime

ADDR = '192.168.56.100'
PORT = '3306'
DB = 'INDEX_DUCK'
ID = 'root'
PW = 'root'

db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()

### 1. 종목정보덤프
print(">> 1. 시가총액 5천억 이상 ticker 덤프")

# 1.0. 기존 데이터 제거
print("1.0. 기존 데이터 제거")
cursor.execute("TRUNCATE cap")
cursor.execute("TRUNCATE stocks_price")
db.commit()

# 1.1 시가총액 업데이트
print("1.1. 시가총액 업데이트")
capDf = stock.get_market_cap_by_ticker('20211031')
capDf.index.names = ['ticker']
capDf = capDf.rename(columns={'종가':'close', '시가총액':'cap'}).drop(['거래량', '거래대금', '상장주식수'], axis=1)
capDf = capDf[capDf['cap'] >= 500000000000]
db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
conn = db_connection.connect()
capDf.to_sql(name='cap', con=db_connection, if_exists='append', index=True, index_label="ticker")
conn.close()
#### > 구매한 티커는 별도로 관리

# 1.2. 티커리스트 조회
print("1.2. 티커리스트 조회")
cursor.execute("SELECT ticker FROM cap WHERE cap >= '500000000000'")
tickers = list(map(lambda x: x[0], cursor.fetchall()))
db.close()

# 1.3. 기간 설정
print("1.3. 기간 설정")
start = '20210601'
end = str(datetime.now().date()).replace('-', '')
print("기간: (%s - %s)" %(start, end))

# 1.4. 새로운 데이터 업데이트
print("1.4. 새로운 데이터 업데이트 (%s - %s)" %(start, end))
for ticker in tickers:
  try:
    df = stock.get_market_ohlcv_by_date(start, end, ticker)
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

# 1.5. 거래이상 종목제거
print("1.5. 거래이상종목제거")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("DELETE FROM stocks_price WHERE ticker IN (SELECT DISTINCT(ticker) FROM stocks_price WHERE volume = 0)")
db.commit()
db.close()