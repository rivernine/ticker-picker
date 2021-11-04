from sqlalchemy import create_engine
import pymysql
import pandas as pd
from pykrx import stock
import time
from datetime import datetime
import traceback

ADDR = '192.168.56.100'
PORT = '3306'
DB = 'GLOBAL'
ID = 'root'
PW = 'root'

db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()

### 2. 볼린저밴드 초기세팅
print(">> 2. Init bollinger band")

# 2.0. 기존 데이터 제거
print("2.0. Delete old data")
cursor.execute("TRUNCATE boll")
db.commit()

# 2.1. 심볼리스트 조회
print("2.1. Get symbol list")
cursor.execute("SELECT DISTINCT symbol FROM stocks_price")
symbols = list(map(lambda x: x[0], cursor.fetchall()))

# 2.2. 기간 설정
print("2.2. Set period")
start = '20210801'
end = str(datetime.now().date()).replace('-', '')
print("Period: (%s - %s)" %(start, end))

# 2.3. 새로운 데이터 업데이트
print("2.3. Update new data (%s - %s)" %(start, end))
day = 20
for symbol in symbols:
  try:
    cursor.execute("SELECT * FROM stocks_price WHERE symbol = '" + symbol + "' ORDER BY date DESC")
    priceDf = pd.DataFrame(cursor.fetchall())
    priceDf = priceDf.rename(columns={0: 'date', 1:'symbol', 2:'open', 3:'high', 4:'low', 5:'close', 6:'volume'}).drop(['open', 'high', 'low', 'volume'], axis=1)
    # Set Dataframe
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
      
      lo = avg - std * 2
      me = avg
      hi = avg + std * 2
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
    print('ex1', traceback.format_exc(), ex1)
    pass