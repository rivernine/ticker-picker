from sqlalchemy import create_engine
import pymysql
import pandas as pd
from pykrx import stock
import time
from datetime import datetime

ADDR = '192.168.56.100'
PORT = '3306'
DB = 'GLOBAL'
ID = 'root'
PW = 'root'

db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()

### 3. MFI 초기세팅
print(">> 3. Init MFI")

# 3.0. 기존 데이터 제거
print("3.0. Delete old data")
cursor.execute("TRUNCATE mfi")
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

# 3.3. 새로운 데이터 업데이트
print("2.3. Update new data (%s - %s)" %(start, end))
day = 10
print(symbols)
for symbol in symbols:
  try:
    cursor.execute("SELECT * FROM stocks_price WHERE symbol = '" + symbol + "' ORDER BY date DESC")
    priceDf = pd.DataFrame(cursor.fetchall())
    priceDf = priceDf.rename(columns={0: 'date', 1:'symbol', 2:'open', 3:'high', 4:'low', 5:'close', 6:'volume'})
    # Set Dataframe
    priceDf['tp'] = 0.0
    priceDf['mfi'] = 0.0
    priceDf['mfi_diff'] = 0.0
    # Set typical price
    for idx in range(0, len(priceDf)):
      row = priceDf.iloc[idx]
      priceDf.at[idx, 'tp'] = (row['high'] + row['low'] + row['close']) / 3
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
      MFI = positiveRMF / (positiveRMF + negativeRMF) * 100
      priceDf.at[idx, 'mfi'] = MFI
      if idx > 0:
        priceDf.at[idx - 1, 'mfi_diff'] = priceDf.iloc[idx - 1]['mfi'] - MFI
    mfiDf = priceDf.reset_index().set_index('date').drop(['index', 'open', 'high', 'low', 'close', 'volume'], axis=1)
    db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
    conn = db_connection.connect()
    mfiDf.to_sql(name='mfi', con=db_connection, if_exists='append', index=True, index_label="date")        
    conn.close()
    db.commit()
  except Exception as ex1:
    print('ex1', ex1, symbol)
    pass
db.close()