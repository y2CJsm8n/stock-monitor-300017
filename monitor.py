import akshare as ak
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
from datetime import datetime

STOCK_CODE = "300017"
PRICE_HIGH = 17.35
PRICE_LOW = 16.90

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def get_stock_price():
    try:
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == STOCK_CODE]
        if stock.empty:
            print(f"[{datetime.now()}] 未找到股票代码: {STOCK_CODE}")
            return None
        price = float(stock['最新价'].iloc[0])
        return round(price, 2)
    except Exception as e:
        print(f"[{datetime.now()}] 获取股价失败: {e}")
        return None

def send_alert(price, reason):
    subject = f"【股票提醒】{STOCK_CODE} 触发{reason}线"
    body = f"""
股票代码：{STOCK_CODE}（网宿科技）
当前价格：{price} 元
触发条件：{reason}
触发时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
提醒线：{PRICE_HIGH if reason == '突破' else PRICE_LOW} 元
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        print(f"[{datetime.now()}] 邮件发送成功！价格: {price}")
    except Exception as e:
        print(f"[{datetime.now()}] 邮件发送失败: {e}")

def main():
    price = get_stock_price()
    if price is None:
        return

    print(f"[{datetime.now()}] 当前股价: {price}")

    status_file = "last_status.txt"
    last_status = ""
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            last_status = f.read().strip()

    current_status = "normal"
    if price >= PRICE_HIGH:
        current_status = "above_high"
        if last_status != "above_high":
            send_alert(price, "突破")
    elif price <= PRICE_LOW:
        current_status = "below_low"
        if last_status != "below_low":
            send_alert(price, "破位")
    else:
        current_status = "normal"

    with open(status_file, "w") as f:
        f.write(current_status)

if __name__ == "__main__":
    main()
