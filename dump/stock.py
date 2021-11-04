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
print(">> 1. DUMP cap >= 500000000000 & KOSPI")

# 1.0. 기존 데이터 제거
print("1.0. Delete old data")
cursor.execute("TRUNCATE cap")
cursor.execute("TRUNCATE stocks_price")
db.commit()

# 1.1 시가총액 업데이트
print("1.1. Update cap")
# 1.1.1. 매수종목조회
print("1.1.1. Get already bid ticker")
cursor.execute("SELECT ticker FROM bid_basket")
basketTickers = list(map(lambda x: x[0], cursor.fetchall()))
basketTickers.remove('test')
# 1.1.2. 최신데이터call
print("1.1.2. Get new data")
capDf = stock.get_market_cap_by_ticker(str(datetime.now().date()).replace('-', ''), market='KOSPI')
capDf.index.names = ['ticker']
capDf = capDf.rename(columns={'종가':'close', '시가총액':'cap'}).drop(['거래량', '거래대금', '상장주식수'], axis=1)
basketDf = capDf.loc[basketTickers].copy()
capDf = capDf[capDf['cap'] >= 500000000000]
totalDf = pd.concat([basketDf,capDf]).drop_duplicates()
db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
conn = db_connection.connect()
totalDf.to_sql(name='cap', con=db_connection, if_exists='append', index=True, index_label="ticker")
conn.close()

# 1.2. 티커리스트 조회
print("1.2. Get ticker list")
db.commit()
cursor.execute("SELECT ticker FROM cap")
tickers = list(map(lambda x: x[0], cursor.fetchall()))
print(tickers)
db.close()

# 1.3. 기간 설정
print("1.3. Set period")
start = '20210601'
end = str(datetime.now().date()).replace('-', '')
print("period: (%s - %s)" %(start, end))

# 1.4. 새로운 데이터 업데이트
print("1.4. Update new data (%s - %s)" %(start, end))
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
print("1.5. Delete outlier")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("DELETE FROM stocks_price WHERE ticker IN (SELECT DISTINCT(ticker) FROM stocks_price WHERE volume = 0)")
db.commit()
db.close()