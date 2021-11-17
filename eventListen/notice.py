import pandas as pd
import pymysql
from datetime import datetime, timedelta
import traceback
import telegram

# DB 정보
ADDR = '192.168.56.100'
PORT = '3306'
DB = 'INDEX_DUCK'
ID = 'root'
PW = 'root'

# 텔레그램 정보
bot_token = '2070032123:AAG9uPgrcDBRYQApPV1p1I0i4EoQCD3tWiw'
bot = telegram.Bot(token = bot_token)
chat_id = 2065271401

## Boundary
position_bid = 0.1
mfi_bid = 10

### 1. 종목(cap >= 10천억 && KOSPI)조회 및 거래
print("\n>> 1. Get ticker(cap >= 1000000000000 && KOSPI) & Trade")

# 1.1. 기간 설정
print("\n1.1. Set the date")
date = str(datetime.now().date() - timedelta(days=1)).replace('-', '')
print("Date: (%s)" %(date))
try:
  # 1.2. 티커별 종합정보조회
  print("\n1.2. Get info tickers")
  sql = """
  SELECT BOLMFI.*, CAP.cap
  FROM (
    SELECT BOL.*, MFI.tp, MFI.mfi, MFI.mfi_diff
    FROM (
      SELECT * 
      FROM boll 
      WHERE date = %s
      AND period = 20
    ) AS BOL
    JOIN (
      SELECT ticker, tp, mfi, mfi_diff
      FROM mfi
      WHERE date = %s
      AND period = 10
    ) AS MFI
    ON (BOL.ticker = MFI.ticker)
  ) AS BOLMFI
  JOIN (
    SELECT ticker, cap
    FROM cap
  ) AS CAP
  ON (BOLMFI.ticker = CAP.ticker)    
  ORDER BY CAP.cap DESC
  """ % (date, date)
  db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
  cursor = db.cursor()
  cursor.execute(sql)
  db.close()
  sumDf = pd.DataFrame(cursor.fetchall()).rename(columns={0:'date', 1:'ticker', 2:'period', 3:'close', 4:'low', 5:'medium', 6:'high', 7:'bandWidth', 8:'position', 9: 'tp', 10: 'mfi', 11: 'mfi_diff', 12:'cap'})
  sumDf.set_index('ticker', drop=True, inplace=True)
  notice_list = []
  for idx in sumDf.index:    
    row = sumDf.loc[idx].copy()
    ticker = row.name
    if row['position'] <= position_bid and row['mfi'] <= mfi_bid and row['mfi'] > 0 and row['mfi_diff'] > 0:
      notice_list.append('[%s]: %s원, %.2f(MFI), %.2f(bollinger)' %(ticker, row['close'], row['mfi'], row['position']))
  bot.sendMessage(chat_id = chat_id, text='< %s >' %(date))
  for notice in notice_list:
    bot.sendMessage(chat_id = chat_id, text=notice)
except Exception as ex1:
  print('ex1', traceback.format_exc(), ex1)