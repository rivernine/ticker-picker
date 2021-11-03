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
chat_id = bot.getUpdates()[-1].message.chat.id

### Back test 파라미터
## 투자금 / 분할
total_amount, step = 10000000, 5
trade_amount = total_amount / step
## Boundary
position_bid = 0.1
position_ask = 0.8
mfi_bid = 10
mfi_ask = 90

tx_count = 1
### 0. 키움 로그인
print("0. 키움 로그인")
kiwoom_conn = kiwoom.create_connect()

# 0.1. 주문가능금액조회
print("\n0.1. 주문가능금액조회")
my_amount = kiwoom.get_amount(kiwoom_conn)
print("주문가능금액: %s원" %(my_amount))

### 1. 종목(cap >= 5천억 && KOSPI)조회 및 거래
print("\n>> 1. 종목(cap >= 5천억 && KOSPI)조회 및 거래")

# 1.0. 매수종목조회
print("\n1.0. 매수종목조회")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("SELECT * FROM bid_basket")
db.close()
basketDf = pd.DataFrame(cursor.fetchall()).rename(columns={0:'date', 1:'ticker', 2:'price', 3:'volume', 4:'mfi', 5:'position'})
if len(basketDf) > 0:
  basketDf.set_index('ticker', drop=True, inplace=True)
  print(basketDf.index)

# 1.1. 기간 설정
print("\n1.1. 기간 설정")
date = str(datetime.now().date()).replace('-', '')
print("기간: (%s)" %(date))

try:
  # 1.2. 티커별 종합정보조회
  print("\n1.2. 티커별 종합정보조회")
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
    # break
    row = sumDf.loc[idx].copy()
    ticker = row.name
    ############################
    ## BID STEP    
    if row['position'] <= position_bid and row['mfi'] <= mfi_bid and row['mfi'] > 0 and row['mfi_diff'] > 0:
      # 1.3. 매수기회포착
      print("\n1.3. 매수기회포착 (%s)" %(ticker))
      bot.sendMessage(chat_id = chat_id, text="매수기회포착 (%s)" %(ticker))
      # 1.4. 매수여부확인
      print("1.4. 매수여부확인 (%s)" %(ticker))      
      if ticker in basketDf.index:
        print("  [INFO] 이미 매수한 종목입니다. (%s)" %(ticker))
        bot.sendMessage(chat_id = chat_id, text="[INFO] 이미 매수한 종목입니다. (%s)" %(ticker))        
      # 매수
      elif ticker not in basketDf.index and len(basketDf) < step:
        if my_amount >= trade_amount:
          # 1.5. 매수
          print("1.5. 매수 (%s)" %(ticker))      
          print("  [INFO] 매수를 진행합니다. (%s)" %(ticker))
          bot.sendMessage(chat_id = chat_id, text="[INFO] 매수를 진행합니다. (%s)" %(ticker))
          # 1.5.1. 매수수량계산
          print("1.5.1. 매수수량계산 (%s)" %(ticker))      
          price = row['close']
          volume = round(trade_amount // price)
          print("%s: %s원 %s주" %(ticker, price, volume))
          if volume > 0:
            # 1.5.2. 키움증권매수
            print("1.5.2. 키움증권매수 (%s)" %(ticker))                  
            if kiwoom.get_status(kiwoom_conn):
              kiwoom.bid_market(kiwoom_conn, tx_count, ticker, volume)
            else:
              kiwoom_conn = kiwoom.create_connect()
              kiwoom.bid_market(kiwoom_conn, tx_count, ticker, volume)
            # 1.5.3. 매수내역기록
            print("1.5.3. 매수내역기록 (%s, %s)" %(date, ticker))    
            db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
            cursor = db.cursor()
            cursor.execute("INSERT INTO bid_basket (date, ticker, price, volume, mfi, position) VALUES (%s, '%s', %s, %s, %s, %s)" %(date, ticker, price, volume, row['mfi'], row['position']))
            cursor.execute("INSERT INTO history (date, ticker, status, bid_price, volume) VALUES (%s, '%s', 'bid', %s, %s)" %(date, ticker, price, volume))
            db.commit()
            db.close()
            print("  [SUCCESS] 매수완료 (%s)" %(ticker))
            bot.sendMessage(chat_id = chat_id, text="[SUCCESS] 매수완료 (%s)" %(ticker))
            bot.sendMessage(chat_id = chat_id, text="(date, ticker, status, bid_price, ask_price, volume, pnl, realized_pnl)")
            bot.sendMessage(chat_id = chat_id, text="(%s, %s, %s, %s, %s, %s, %s, %s)" %(date, ticker, 'bid', price, "NULL", volume, "NULL", "NULL"))
            tx_count += 1
          else:
            print("  [ERROR] 금액이 %s원 이상입니다." %(trade_amount))
            bot.sendMessage(chat_id = chat_id, text="[ERROR] 금액이 %s원 이상입니다." %(trade_amount))
        else:
          print("  [ERROR] 잔액이 부족합니다. 주문가능금액: %s원" %(my_amount))
          bot.sendMessage(chat_id = chat_id, text="[ERROR] 잔액이 부족합니다. 주문가능금액: %s원" %(my_amount))
    ############################
    ## ASK STEP    
    if ticker in basketDf.index:      
      price = row['close']
      info = basketDf.loc[ticker]
      bid_price = info['price']
      pnl = (1 - (bid_price / price)) * 100
      if row['position'] >= position_ask or row['mfi'] >= mfi_ask:
        # 1.6. 매도기회포착
        print("\n1.6. 매도기회포착 (%s)" %(ticker))
        bot.sendMessage(chat_id = chat_id, text="매도기회포착 (%s)" %(ticker))
        # 1.7. 매도
        print("1.7. 매도 (%s)" %(ticker))      
        print("  [INFO] 매도를 진행합니다. (%s)" %(ticker))
        bot.sendMessage(chat_id = chat_id, text="[INFO] 매도를 진행합니다. (%s)" %(ticker))
        # 1.7.1. 매도수량계산
        print("1.7.1. 매도수량계산 (%s)" %(ticker))
        volume = info['volume']
        print("%s: %s원 %s주" %(ticker, price, volume))
        # 1.7.1. 키움증권매도
        print("1.7.2. 키움증권매도 (%s)" %(ticker))  
        if kiwoom.get_status(kiwoom_conn):
          kiwoom.ask_market(kiwoom_conn, tx_count, ticker, volume)
        else:
          kiwoom_conn = kiwoom.create_connect()
          kiwoom.ask_market(kiwoom_conn, tx_count, ticker, volume)
        # 1.7.2. 매도내역기록
        print("1.7.2. 거래내역기록 (%s, %s)" %(date, ticker))      
        db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
        cursor = db.cursor()
        cursor.execute("DELETE FROM bid_basket WHERE ticker = %s" %(ticker))
        cursor.execute("INSERT INTO history (date, ticker, status, bid_price, ask_price, volume, pnl, realized_pnl) VALUES (%s, '%s', 'ask', %s, %s, %s, %s, %s)" %(date, ticker, bid_price, price, volume, pnl, volume * pnl * 0.01))
        db.commit()
        db.close()
        print("  [SUCCESS] 매도완료 (%s)" %(ticker))
        bot.sendMessage(chat_id = chat_id, text="[SUCCESS] 매도완료 (%s)" %(ticker))
        bot.sendMessage(chat_id = chat_id, text="(date, ticker, status, bid_price, ask_price, volume, pnl, realized_pnl)")
        bot.sendMessage(chat_id = chat_id, text="(%s, %s, %s, %s, %s, %s, %s, %s)" %(date, ticker, 'ask', bid_price, price, volume, pnl, volume * pnl * 0.01))
        tx_count += 1
except Exception as ex1:
  print('ex1', traceback.format_exc(), ex1)