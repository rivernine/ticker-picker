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

### 2. 볼린저밴드 최신화
print(">> 2. Update bollinger band")

# 2.0. 티커 조회
print("2.0. Get ticker list")
cursor.execute("SELECT DISTINCT ticker FROM stocks_price")
tickers = list(map(lambda x: x[0], cursor.fetchall()))

# 2.1. 업데이트 기간 설정
print("2.1. Set the date")
date = str(datetime.now().date()).replace('-', '')
print("Date: (%s)" %(date))

# 2.2. 기존 데이터 제거
print("2.2. Delete old data (%s)" %(date))
cursor.execute("DELETE FROM boll WHERE date =" + date)
db.commit()

# 2.3. 새로운 데이터 업데이트
print("2.3. Update new data (%s)" %(date))
day = 20
print(tickers)
for ticker in tickers:
  try:
    # Get ticker's price
    cursor.execute("SELECT * FROM stocks_price WHERE ticker = '" + ticker + "' AND date <= '" + date + "' ORDER BY date DESC LIMIT " + str(day + 1))
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
    bollDf[:1].to_sql(name='boll', con=db_connection, if_exists='append', index=True, index_label="date")        
    conn.close()
    db.commit()
  except Exception as ex1:
    print('ex1', ex1)
    pass