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
channel_chat_id = -1001722034898
## Boundary
position_bid = 0.1
position_ask = 0.8
mfi_bid_lv1 = 40
mfi_bid_lv2 = 30
mfi_bid_lv3 = 20
mfi_bid_lv4 = 10
mfi_ask = 90

### 1. 종목조회
print("\n>> 1. Get symbol")

# 1.1. 기간 설정
print("\n1.1. Set the date")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT date FROM stocks_price ORDER BY date DESC LIMIT 1")
date = str(cursor.fetchall()[0][0])
db.close()
# date = "20211020"
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
      WHERE date = '%s'
    ) AS BOL
    JOIN (
      SELECT symbol, tp, mfi, mfi_diff
      FROM mfi
      WHERE date = '%s'
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
  print(list(sumDf.index))
  lv1, lv2, lv3, lv4 = "", "", "", ""

  for idx in sumDf.index:        
    row = sumDf.loc[idx].copy()
    symbol = row.name
    ############################
    ## BID STEP    
    if row['position'] <= position_bid and row['mfi'] > 0 and row['mfi_diff'] > 0:
      if row['mfi'] <= mfi_bid_lv4:
        lv4 += "symbol: %s, boll: %.2f, MFI: %.2f\n" %(symbol, row['position'], row['mfi'])
      elif row['mfi'] <= mfi_bid_lv3:
        lv3 += "symbol: %s, boll: %.2f, MFI: %.2f\n" %(symbol, row['position'], row['mfi'])
      elif row['mfi'] <= mfi_bid_lv2:
        lv2 += "symbol: %s, boll: %.2f, MFI: %.2f\n" %(symbol, row['position'], row['mfi'])
      elif row['mfi'] <= mfi_bid_lv1:
        lv1 += "symbol: %s, boll: %.2f, MFI: %.2f\n" %(symbol, row['position'], row['mfi'])
    
    ############################
    ## ASK STEP    
    if symbol in ['NRGU, BTC/KRW']:      
      if row['mfi'] >= mfi_ask:
        # 2.1. 매도기회포착
        print("\n2.1. It's time to Ask!!! (%s)" %(symbol))
        bot.sendMessage(chat_id = chat_id, text="[%s] 매도기회포착 (%s)" %(symbol))
        bot.sendMessage(chat_id = chat_id, text="MFI: %.2f" %(row['mfi']))
        bot.sendMessage(chat_id = channel_chat_id, text="[%s] 매도기회포착 (%s)" %(symbol))
        bot.sendMessage(chat_id = channel_chat_id, text="MFI: %.2f" %(row['mfi']))

  # 3.1. 매수기회포착
  if len(lv1) > 0 or len(lv2) > 0 or len(lv3) > 0 or len(lv4) > 0:
    print("\n 3.1 It's time to bid !!!")
    bot.sendMessage(chat_id = chat_id, text="[%s] 매수기회포착" %(date))
    bot.sendMessage(chat_id = channel_chat_id, text="[%s] 매수기회포착" %(date))
  if len(lv1) > 0:
    print("Level 1")
    print(lv1)
    bot.sendMessage(chat_id = chat_id, text="[Level 1]")
    bot.sendMessage(chat_id = chat_id, text=lv1)
    bot.sendMessage(chat_id = channel_chat_id, text="[Level 1]")
    bot.sendMessage(chat_id = channel_chat_id, text=lv1)
  if len(lv2) > 0:
    print("Level 2")
    print(lv2)
    bot.sendMessage(chat_id = chat_id, text="[Level 2]")
    bot.sendMessage(chat_id = chat_id, text=lv2)
    bot.sendMessage(chat_id = channel_chat_id, text="[Level 2]")
    bot.sendMessage(chat_id = channel_chat_id, text=lv2)
  if len(lv3) > 0:
    print("Level 3")
    print(lv3)
    bot.sendMessage(chat_id = chat_id, text="[Level 3]")
    bot.sendMessage(chat_id = chat_id, text=lv3)
    bot.sendMessage(chat_id = channel_chat_id, text="[Level 3]")
    bot.sendMessage(chat_id = channel_chat_id, text=lv3)
  if len(lv4) > 0:
    print("Level 4")
    print(lv4)
    bot.sendMessage(chat_id = chat_id, text="[Level 4]")
    bot.sendMessage(chat_id = chat_id, text=lv4)
    bot.sendMessage(chat_id = channel_chat_id, text="[Level 4]")
    bot.sendMessage(chat_id = channel_chat_id, text=lv4)
except Exception as ex1:
  print('ex1', traceback.format_exc(), ex1)

# SELECT BOLMFI.*
# FROM (
#   SELECT BOL.*, MFI.tp, MFI.mfi, MFI.mfi_diff
#   FROM (
#     SELECT * 
#     FROM boll 
#     WHERE date = "20211020"
#   ) AS BOL
#   JOIN (
#     SELECT symbol, tp, mfi, mfi_diff
#     FROM mfi
#     WHERE date = "20211020"
#   ) AS MFI
#   ON (BOL.symbol = MFI.symbol)
# ) AS BOLMFI
# WHERE mfi <= 40
# AND mfi > 0
# AND position <= 0.1
# AND mfi_diff > 0
# ;