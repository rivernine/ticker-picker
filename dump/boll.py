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

### 2. 볼린저밴드 초기세팅
print(">> 2. 볼린저밴드 초기세팅")

# 2.0. 기존 데이터 제거
print("2.0. 기존 데이터 제거")
cursor.execute("TRUNCATE boll")
db.commit()

# 2.1. 티커리스트 조회
print("2.1. 티커리스트 조회")
cursor.execute("SELECT DISTINCT ticker FROM stocks_price")
tickers = list(map(lambda x: x[0], cursor.fetchall()))

# 2.2. 기간 설정
print("2.2. 기간 설정")
start = '20210601'
end = str(datetime.now().date()).replace('-', '')
print("기간: (%s - %s)" %(start, end))

# 2.3. 새로운 데이터 업데이트
print("2.3. 새로운 데이터 업데이트 (%s - %s)" %(start, end))
day = 20
for ticker in tickers:
  try:
    # Get ticker's price
    cursor.execute("SELECT * FROM stocks_price WHERE ticker = '" + ticker + "' ORDER BY date DESC")
    priceDf = pd.DataFrame(cursor.fetchall())
    priceDf = priceDf.rename(columns={0: 'date', 1:'ticker', 2:'open', 3:'high', 4:'low', 5:'close', 6:'volume'}).drop(['open', 'high', 'low', 'volume'], axis=1)
    # Set Dataframe
    priceDf['period'] = day
    priceDf['low'] = 0
    priceDf['medium'] = 0
    priceDf['high'] = 0
    priceDf['bandWidth'] = 0.0
    priceDf['position'] = 0.0
    # Set bandWidth, Bollinger
    for idx in range(0, len(priceDf)):
      if idx + day > len(priceDf) - 1:
        continue
      copyDf = priceDf[idx:idx+day].loc[:, 'close'].copy()
      avg = copyDf.mean()
      std = copyDf.std()
      
      lo = round(avg - std * 2)
      me = round(avg)
      hi = round(avg + std * 2)
      bw = (hi - lo) / me
      pos = (priceDf.iloc[idx]['close'] - lo) / (hi - lo)
      priceDf.at[idx, 'low'] = lo
      priceDf.at[idx, 'medium'] = me
      priceDf.at[idx, 'high'] = hi
      priceDf.at[idx, 'bandWidth'] = bw
      priceDf.at[idx, 'position'] = pos

    bollDf = priceDf.reset_index().set_index('date').drop(['index'], axis=1)
    
    db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
    conn = db_connection.connect()
    bollDf.to_sql(name='boll', con=db_connection, if_exists='append', index=True, index_label="date")        
    conn.close()
  except Exception as ex1:
    print('ex1', ex1)
    pass