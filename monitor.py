import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
from datetime import datetime
import time
import re

STOCK_CODE = "300017"
PRICE_HIGH = 17.35
PRICE_LOW = 16.90

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def get_stock_price(retry=3):
    for i in range(retry):
        try:
            print(f"[{datetime.now()}] 尝试获取股价 (第 {i+1} 次)...")
            # 使用新浪财经 API
            url = f"https://hq.sinajs.cn/list=sz{STOCK_CODE}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "gbk"
            
            content = response.text
            if not content or "var hq_str" not in content:
                print(f"[{datetime.now()}] 获取数据失败: 响应为空")
                return None
            
            # 解析数据
            data = content.split('"')[1] if '"' in content else content.split('=')[1].strip().strip('"')
            parts = data.split(',')
            
            if len(parts) < 3:
                print(f"[{datetime.now()}] 数据格式错误")
                return None
            
            price = float(parts[3])  # 当前价格
            return round(price, 2)
        except Exception as e:
            print(f"[{datetime.now()}] 获取股价失败 (尝试 {i+1}/{retry}): {e}")
            if i < retry - 1:
                time.sleep(3)
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
