import pandas as pd
import pymysql
from datetime import datetime, timedelta
import traceback
import telegram

# DB 정보
ADDR = '192.168.56.100'
PORT = '3306'
DB = 'GLOBAL'
ID = 'root'
PW = 'root'

# 텔레그램 정보
bot_token = '2023613321:AAHCb61s8LZoCjRqSt9w-HOeGVh2jPOQ3go'
bot = telegram.Bot(token = bot_token)
chat_id = 2065271401

## Boundary
position_bid = 0.1
position_ask = 0.8
mfi_bid = 30
mfi_ask = 90

### 1. 종목조회
print("\n>> 1. Get symbol")

# 1.1. 기간 설정
print("\n1.1. Set the date")
date = str(datetime.now().date() - timedelta(days=1)).replace('-', '')
# date = "20211029"
print("Date: (%s)" %(date))

try:
  # 1.2. 티커별 종합정보조회
  print("\n1.2. Get info tickers")
  sql = """
  SELECT BOLMFI.*
  FROM (
    SELECT BOL.*, MFI.tp, MFI.mfi, MFI.mfi_diff
    FROM (
      SELECT * 
      FROM boll 
      WHERE date = %s
    ) AS BOL
    JOIN (
      SELECT symbol, tp, mfi, mfi_diff
      FROM mfi
      WHERE date = %s
    ) AS MFI
    ON (BOL.symbol = MFI.symbol)
  ) AS BOLMFI
  """ % (date, date)
  
  db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
  cursor = db.cursor()
  cursor.execute(sql)
  db.close()
  sumDf = pd.DataFrame(cursor.fetchall()).rename(columns={0:'date', 1:'symbol', 2:'close', 3:'low', 4:'medium', 5:'high', 6:'bandWidth', 7:'position', 8: 'tp', 9: 'mfi', 10: 'mfi_diff'})
  sumDf.set_index('symbol', drop=True, inplace=True)
  for idx in sumDf.index:        
    row = sumDf.loc[idx].copy()
    symbol = row.name
    print(symbol)
    ############################
    ## BID STEP    
    if row['position'] <= position_bid and row['mfi'] <= mfi_bid and row['mfi'] > 0 and row['mfi_diff'] > 0:
      # 2.1. 매수기회포착
      print("\n2.1. It's time to Bid!!! (%s)" %(symbol))
      bot.sendMessage(chat_id = chat_id, text="[%s] 매수기회포착 (%s)" %(date, symbol))
      bot.sendMessage(chat_id = chat_id, text="POSITION: %.4f, MFI: %.4f, MFI_DIFF: %.4f" %(row['position'], row['mfi'], row['mfi_diff']))
    
    ############################
    ## ASK STEP    
    if symbol in ['NRGU, BTC/KRW']:      
      if row['mfi'] >= mfi_ask:
        # 3.1. 매도기회포착
        print("\n3.1. It's time to Ask!!! (%s)" %(symbol))
        bot.sendMessage(chat_id = chat_id, text="[%s] 매도기회포착 (%s)" %(symbol))
        bot.sendMessage(chat_id = chat_id, text="MFI: %.4f" %(row['mfi']))
except Exception as ex1:
  print('ex1', traceback.format_exc(), ex1)