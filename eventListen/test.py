import pandas as pd
import pymysql
from datetime import datetime
import traceback
import kiwoom
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

### Back test 파라미터
## 투자금 / 분할
total_amount, step = 10000000, 5
trade_amount = total_amount / step
trade_amount = 300000
## Boundary
position_bid = 0.1
position_ask = 0.8
mfi_bid = 10
mfi_ask = 90

tx_count = 1

### 0. 키움 로그인
print("0. Kiwoom Login")
kiwoom_conn = kiwoom.create_connect()

# 0.1. 주문가능금액조회
print("\n0.1. Get my amount")
my_amount = kiwoom.get_amount(kiwoom_conn)
print("My amount: %s" %(my_amount))

### 1. 종목(cap >= 5천억 && KOSPI)조회 및 거래
print("\n>> 1. Get ticker(cap >= 500000000000 && KOSPI) & Trade")

# 1.0. 매수종목조회
print("\n1.0. Get bid basket")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT * FROM bid_basket")
db.close()
basketDf = pd.DataFrame(cursor.fetchall()).rename(columns={0:'date', 1:'ticker', 2:'price', 3:'volume', 4:'mfi', 5:'position'})
if len(basketDf) > 0:
  basketDf.set_index('ticker', drop=True, inplace=True)
  print(basketDf.index)

# 1.1. 기간 설정
print("\n1.1. Set the date")
date = str(datetime.now().date()).replace('-', '')
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
  for idx in sumDf.index:    
    row = sumDf.loc[idx].copy()
    ticker = row.name
    ############################
    ## BID STEP    
    if row['position'] <= position_bid and row['mfi'] <= mfi_bid and row['mfi'] > 0 and row['mfi_diff'] > 0:
      # 2.1. 매수기회포착
      print("\n2.1. It's time to Bid!!! (%s)" %(ticker))
      # bot.sendMessage(chat_id = chat_id, text="[%s] 매수기회포착 (%s)" %(date, ticker))
      # 2.2. 매수여부확인
      print("2.2. Check already bid (%s)" %(ticker))      
      if ticker in basketDf.index:
        print("  [INFO] Already bid... (%s)" %(ticker))
        # bot.sendMessage(chat_id = chat_id, text="[INFO] 이미 매수한 종목입니다. (%s)" %(ticker))        
      # 매수
      elif ticker not in basketDf.index and len(basketDf) < step:
        # bot.sendMessage(chat_id = chat_id, text="[%s] 매수기회포착 (%s)" %(date, ticker))
        if my_amount >= trade_amount:
          # 2.3. 매수
          print("2.3. Bid (%s)" %(ticker))      
          print("  [INFO] Let's Bid!! (%s)" %(ticker))
          # bot.sendMessage(chat_id = chat_id, text="[INFO] 매수를 진행합니다. (%s)" %(ticker))
          # 2.3.1. 매수수량계산
          print("2.3.1. Calculate bid volume (%s)" %(ticker))      
          price = row['close']
          volume = round(trade_amount // price)
          print("  [%s] %sKRW : %s" %(ticker, price, volume))
        else:
          print("  [ERROR] Not enough money. %s" %(my_amount))
          # bot.sendMessage(chat_id = chat_id, text="[ERROR] 잔액이 부족합니다. 주문가능금액: %s원" %(my_amount))
    ############################
    ## ASK STEP    
    if ticker in basketDf.index:      
      price = row['close']
      info = basketDf.loc[ticker]
      bid_price = info['price']
      pnl = (1 - (bid_price / price)) * 100
      if row['position'] >= position_ask or row['mfi'] >= mfi_ask:
        # 3.1. 매도기회포착
        print("\n3.1. It's time to Ask!!! (%s)" %(ticker))
        # bot.sendMessage(chat_id = chat_id, text="[%s] 매도기회포착 (%s)" %(date, ticker))
        # 3.2. 매도
        print("3.2. Ask (%s)" %(ticker))      
        print("  [INFO] Let's Ask!! (%s)" %(ticker))
        # bot.sendMessage(chat_id = chat_id, text="[INFO] 매도를 진행합니다. (%s)" %(ticker))
        # 3.2.1. 매도수량계산
        print("3.2.1. Calculate ask volume (%s)" %(ticker))
        volume = info['volume']
        print("  [%s] %sKRW : %s" %(ticker, price, volume))
        print("  [SUCCESS] Complete the ask (%s)" %(ticker))
except Exception as ex1:
  print('ex1', traceback.format_exc(), ex1)


# SELECT BOLMFI.*, CAP.cap
# FROM (
#   SELECT BOL.*, MFI.tp, MFI.mfi, MFI.mfi_diff
#   FROM (
#     SELECT * 
#     FROM boll 
#     WHERE date = "20211105"
#     AND period = 20
#   ) AS BOL
#   JOIN (
#     SELECT ticker, tp, mfi, mfi_diff
#     FROM mfi
#     WHERE date = "20211105"
#     AND period = 10
#   ) AS MFI
#   ON (BOL.ticker = MFI.ticker)
# ) AS BOLMFI
# JOIN (
#   SELECT ticker, cap
#   FROM cap
# ) AS CAP
# ON (BOLMFI.ticker = CAP.ticker)    
# WHERE mfi <= 10
# AND mfi_diff > 0
# AND position <= 0.1
# ORDER BY CAP.cap DESC  