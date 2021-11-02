# 사용자 정보 가져오기
from pykiwoom.kiwoom import *

def create_connect():
  kiwoom = Kiwoom()
  kiwoom.CommConnect(block=True)
  return kiwoom

def bid_limit(kiwoom, ticker, volume, price):
  state = kiwoom.GetConnectState()
  if state == 0:
    print("연결을 확인하세요.")
    return
  elif state == 1:
    print("연결완료. 지정가매수를 진행합니다.")
    accounts = kiwoom.GetLoginInfo("ACCNO")
    stock_account = accounts[0]
    kiwoom.SendOrder("지정가매수", "0101", stock_account, 1, ticker, volume, price, "00", "")   

def bid_market(kiwoom, ticker, volume):
  state = kiwoom.GetConnectState()
  if state == 0:
    print("연결을 확인하세요.")
    return
  elif state == 1:
    print("연결완료. 시장가매수를 진행합니다.")
    accounts = kiwoom.GetLoginInfo("ACCNO")
    stock_account = accounts[0]
    kiwoom.SendOrder("시장가매수", "0101", stock_account, 1, ticker, volume, 0, "03", "")

def ask_market(kiwoom, ticker, volume):
  state = kiwoom.GetConnectState()
  if state == 0:
    print("연결을 확인하세요.")
    return
  elif state == 1:
    print("연결완료. 시장가매도를 진행합니다.")
    accounts = kiwoom.GetLoginInfo("ACCNO")
    stock_account = accounts[0]
    kiwoom.SendOrder("시장가매도", "0101", stock_account, 2, ticker, volume, 0, "03", "")

def test():
  print("test")
