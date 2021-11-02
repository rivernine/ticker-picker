import kiwoom
print("0. 키움 로그인")
try:
  kiwoom_conn = kiwoom.create_connect()

  # 0.1. 주문가능금액조회
  print("0.1. 주문가능금액조회")
  my_amount = kiwoom.get_amount(kiwoom_conn)
  print("주문가능금액: %s원" %(my_amount))
except Exception as ex:
  print(ex)