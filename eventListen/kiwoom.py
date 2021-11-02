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
                          계좌번호="8011076211",
                          비밀번호="1234",
                          조회구분="2",
                          output="예수금상세현황",
                          next=0
                          )
  return int(df['주문가능금액'][0])

def bid_limit(kiwoom, ticker, volume, price):
  print("지정가매수를 진행합니다.")
  accounts = kiwoom.GetLoginInfo("ACCNO")
  stock_account = accounts[0]
  return kiwoom.SendOrder("지정가매수", "0101", stock_account, 1, ticker, volume, price, "00", "")   

def bid_market(kiwoom, ticker, volume):
  print("시장가매수를 진행합니다.")
  accounts = kiwoom.GetLoginInfo("ACCNO")
  stock_account = accounts[0]
  return kiwoom.SendOrder("시장가매수", "0101", stock_account, 1, ticker, volume, 0, "03", "")

def ask_limit(kiwoom, ticker, volume, price):
  print("지정가매도를 진행합니다.")
  accounts = kiwoom.GetLoginInfo("ACCNO")
  stock_account = accounts[0]
  return kiwoom.SendOrder("지정가매도", "0101", stock_account, 2, ticker, volume, price, "00", "")

def ask_market(kiwoom, ticker, volume):
  print("시장가매도를 진행합니다.")
  accounts = kiwoom.GetLoginInfo("ACCNO")
  stock_account = accounts[0]
  return kiwoom.SendOrder("시장가매도", "0101", stock_account, 2, ticker, volume, 0, "03", "")

