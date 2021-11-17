import FinanceDataReader as fdr
import yfinance as yf
from sqlalchemy import create_engine
import pymysql
import pandas as pd
from pykrx import stock
import time
from datetime import datetime, timedelta
import ccxt

ADDR = '192.168.56.100'
PORT = '3306'
DB = 'GLOBAL'
ID = 'root'
PW = 'root'

nasdaq = list(fdr.StockListing('NASDAQ')['Symbol'])[:100]
sp = list(fdr.StockListing('SP500')['Symbol'])[:100]
cust = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'FB', 'BRK-A', 'NVDA', 'V', 'JPM', 'JNJ', 'UNH', 'WMT', 'HD', 'BAC', 'MA', 'PG', 'DIS', 'ADBE', 'NFLX', 'PYPL', 'CRM', 'XOM', 'ORCL', 'NKE', 'CMCSA', 'PFE', 'TMO', 'LLY', 'KO'
, 'CSCO', 'ABT', 'DHR', 'CVX', 'PEP', 'VZ', 'COST', 'AVGO', 'MRK', 'WFC', 'INTC', 'ABBV', 'TXN', 'MS', 'T', 'UPS', 'MCD', 'NEE', 'INTU', 'LOW', 'SCHW', 'UNP', 'PM', 'HON', 'QCOM', 'AMD', 'TMUS', 'AXP', 'MRNA', 'BLK', 'C'
, 'GS', 'RTX', 'NOW', 'SBUX', 'CHTR', 'AMT', 'BMY', 'TGT', 'BA', 'ISRG', 'AMAT', 'SQ', 'EL', 'AMGN', 'CVS', 'GE', 'IBM', 'CAT', 'DE', 'SPGI', 'PLD', 'ABNB', 'MMM', 'ANTM', 'LMT', 'SYK', 'SNOW'
, 'COP', 'ZTS', 'BKNG', 'BX', 'ADI', 'USB', 'ADP', 'PNC', 'MO', 'UBER', 'SNAP', 'TFC', 'DELL', 'MMC', 'COIN', 'GILD', 'MDLZ', 'GM', 'ZM', 'SHW' ]
etc = ['NRGU', 'FNGU', 'TQQQ']
coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
# symbols = list(set(nasdaq + sp + etc))
symbols = list(set(cust + etc))

### 1. 나스닥, SP500, 기타종목 최신화
print(">> 1. Update Nasdaq, sp500, etc")

### 2. 기존 데이터 제거
print("2. Delete old data")
db = pymysql.connect(host=ADDR, port=int(PORT), user=ID, passwd=PW, db=DB, charset='utf8')
cursor = db.cursor()
cursor.execute("TRUNCATE stocks_price")
db.commit()

### 3. BTC
binance = ccxt.binance()
for coin in coins:
  ohlcv = binance.fetch_ohlcv(coin, timeframe='1d', limit=100)
  df = pd.DataFrame(ohlcv, columns = ['date', 'open', 'high', 'low', 'close', 'volume'])
  df['date'] = pd.to_datetime(df['date'], unit='ms')
  df = df.set_index(['date'])
  db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
  conn = db_connection.connect()
  df.to_sql(name='stocks_price', con=db_connection, if_exists='append', index=True, index_label="date")
  conn.close()
  db.commit()  
# df = fdr.DataReader('BTC/KRW', '2021-07-01').rename(columns={'Open': 'open', 'High':'high', 'Low':'low', 'Close':'close', 'Volume':'volume'}).drop(['Change'], axis=1)
# df['symbol'] = 'BTC/KRW'
# df = df[['symbol', 'open', 'high', 'low', 'close', 'volume']]
# db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
# conn = db_connection.connect()
# df.to_sql(name='stocks_price', con=db_connection, if_exists='append', index=True, index_label="date")
# conn.close()
# db.commit()

### 4. GLOBAL
print(symbols)
for idx in range(0, len(symbols), 50):
  symbol_list = symbols[idx:idx+50]
  df = yf.download(symbol_list, start = '2021-08-01')
  time.sleep(0.1)
  swapDf = df.swaplevel(0, 1, axis=1)
  for symbol in symbol_list:
    symbolDf = swapDf[symbol].rename(columns={'Open': 'open', 'High':'high', 'Low':'low', 'Close':'close', 'Volume':'volume'}).drop(['Adj Close'], axis=1)
    symbolDf['symbol'] = symbol
    symbolDf = symbolDf[['symbol', 'open', 'high', 'low', 'close', 'volume']]
    try:
      db_connection = create_engine('mysql+pymysql://'+ ID +':'+ PW +'@'+ ADDR +':'+ PORT +'/'+ DB, encoding='utf-8', pool_pre_ping=True)
      conn = db_connection.connect()
      symbolDf.to_sql(name='stocks_price', con=db_connection, if_exists='append', index=True, index_label="date")
      conn.close()
      db.commit()
    except Exception as ex:
      print(ex, symbol)
      pass
db.close()
