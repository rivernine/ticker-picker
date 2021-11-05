# 사용자 정보 가져오기
from pykiwoom.kiwoom import *

def create_connect():
  kiwoom = Kiwoom()
  kiwoom.CommConnect(block=True)
  return kiwoom

def get_status(kiwoom):
  return kiwoom.GetConnectState()

def get_amount(kiwoom):
  df = kiwoom.block_request("opw00001",
                          계좌번호="5989508710",
                          비밀번호="9853",
                          조회구분="2",
                          output="예수금상세현황",
                          next=0
                          )
  return int(df['주문가능금액'][0])

def bid_limit(kiwoom, tx_count, ticker, volume, price):
  print("  [BID_LIMIT] %s | %s KRW | %s" %(ticker, price, volume))
  accounts = kiwoom.GetLoginInfo("ACCNO")
  return kiwoom.SendOrder("지정가매수", str(tx_count).zfill(4), 5989508710, 1, ticker, volume, price, "00", "")   

def bid_market(kiwoom, tx_count, ticker, volume):
  print("  [BID_MARKET] %s | %s" %(ticker, volume))
  accounts = kiwoom.GetLoginInfo("ACCNO")
  return kiwoom.SendOrder("시장가매수", str(tx_count).zfill(4), 5989508710, 1, ticker, volume, 0, "03", "")

def ask_limit(kiwoom, tx_count, ticker, volume, price):
  print("  [ASK_LIMIT] %s | %s KRW | %s" %(ticker, price, volume))
  accounts = kiwoom.GetLoginInfo("ACCNO")
  return kiwoom.SendOrder("지정가매도", str(tx_count).zfill(4), 5989508710, 2, ticker, int(volume), price, "00", "")

def ask_market(kiwoom, tx_count, ticker, volume):
  print("  [ASK_MARKET] %s | %s" %(ticker, volume))
  accounts = kiwoom.GetLoginInfo("ACCNO")
  return kiwoom.SendOrder("시장가매도", str(tx_count).zfill(4), 5989508710, 2, ticker, int(volume), 0, "03", "")

