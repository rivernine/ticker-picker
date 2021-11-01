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

### 3. MFI 최신화
print(">> 3. MFI 최신화")

# 3.0. 티커 조회
print("3.0. 티커 조회")
cursor.execute("SELECT DISTINCT ticker FROM stocks_price")
tickers = list(map(lambda x: x[0], cursor.fetchall()))

# 3.1. 업데이트 기간 설정
print("3.1. 업데이트 기간 설정")
date = str(datetime.now().date()).replace('-', '')
print("기간: (%s)" %(date))

# 3.2. 기존 데이터 제거
print("3.2. 기존 데이터 제거 (%s)" %(date))
cursor.execute("DELETE FROM mfi WHERE date =" + date)
db.commit()

# 3.3. 새로운 데이터 업데이트
print("3.3. 새로운 데이터 업데이트 (%s)" %(date))
day = 10
for ticker in tickers:
  try:
    # Get ticker's price
    cursor.execute("SELECT * FROM stocks_price WHERE ticker = '" + ticker + "' AND date <= '" + date + "' ORDER BY date DESC LIMIT " + str(day + 2))
    priceDf = pd.DataFrame(cursor.fetchall())
    priceDf = priceDf.rename(columns={0: 'date', 1:'ticker', 2:'open', 3:'high', 4:'low', 5:'close', 6:'volume'})
    # Set Dataframe
    priceDf['period'] = day
    priceDf['tp'] = 0
    priceDf['mfi'] = 0
    priceDf['mfi_diff'] = 0
    # Set typical price
    for idx in range(0, len(priceDf)):
      row = priceDf.iloc[idx]
      priceDf.at[idx, 'tp'] = round((row['high'] + row['low'] + row['close']) / 3)
    # Set MFI
    for idx in range(0, len(priceDf)):
      if idx + day > len(priceDf) - 1:
        continue
      positiveRMF = 0
      negativeRMF = 0          
      for i in range(idx, idx + day):
        today = priceDf.iloc[i]
        yesterday = priceDf.iloc[i + 1]
        if today['tp'] > yesterday['tp']:
          positiveRMF += today['tp'] * today['volume']
        elif today['tp'] < yesterday['tp']:
          negativeRMF += today['tp'] * today['volume']
      MFI = round(positiveRMF / (positiveRMF + negativeRMF) * 100)
      priceDf.at[idx, 'mfi'] = MFI
      if idx > 0:
        priceDf.at[idx - 1, 'mfi_diff'] = priceDf.iloc[idx - 1]['mfi'] - MFI
    mfiDf = priceDf.reset_index().set_index('date').drop(['index', 'open', 'high', 'low', 'close', 'volume'], axis=1)
    db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
    conn = db_connection.connect()
    mfiDf[:1].to_sql(name='mfi', con=db_connection, if_exists='append', index=True, index_label="date")        
    conn.close()
  except Exception as ex1:
    print('ex1', ex1, ticker)
    pass
db.close()