from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sqlite3
import urllib.parse
import uuid
import threading
import os
import time
import requests

# --- إعدادات البوت والمالك ---
TELEGRAM_BOT_TOKEN = "8462300261:AAGsdA4BmZNkyytXjqPlvTS2B7g9RO5vhWc"
ADMIN_USER_ID = 6915929098
WEBAPP_URL = "https://poice-production.up.railway.app"

ROOT = Path(__file__).parent
DB_PATH = ROOT / "database.db"

# --- تهيئة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            balance REAL DEFAULT 30.0,
            stars REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gift_links (
            code TEXT PRIMARY KEY,
            amount REAL,
            max_uses INTEGER,
            current_uses INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_gifts (
            user_id TEXT,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_or_create_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, stars FROM users WHERE user_id = ?", (str(user_id),))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance, stars) VALUES (?, 30.0, 0.0)", (str(user_id),))
        conn.commit()
        balance, stars = 30.0, 0.0
    else:
        balance, stars = row[0], row[1]
    conn.close()
    return balance, stars


# --- سيرفر الـ HTTP والـ API الخاص باللعبة ---
class RocketHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path.startswith("/api/"):
            return self.handle_api_get(path, query_params)

        requested = ROOT / path.lstrip("/").split("?", 1)[0]
        if not requested.exists() and not path.startswith("/assets/"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
            except:
                data = {}
            return self.handle_api_post(path, data)
        
        return super().do_POST()

    def handle_api_get(self, path, query_params):
        request_path = path.rstrip("/")

        if "gifts" in request_path:
            payload = json.dumps([{
                "id": "vice-cream-demo",
                "name": "Vice Cream",
                "model_name": "Vice Cream",
                "price": 4.08,
                "price_ton": "4.08",
                "priceTon": 4.08,
                "status": "available",
                "imageUrl": "https://cdn.changes.tg/gifts/models/vice-cream.webp",
                "backdropName": None
            }]).encode("utf-8")
            self.send_json(200, payload)
            return

        if "wallet/balance" in request_path:
            user_id = query_params.get("user_id", ["1"])[0]
            balance, stars = get_or_create_user(user_id)
            payload = json.dumps({
                "availableTON": str(balance),
                "balanceTON": str(balance),
                "starsBalance": str(stars)
            }).encode("utf-8")
            self.send_json(200, payload)
            return

        self.send_json(200, b'{"status": "ok"}')

    def handle_api_post(self, path, data):
        request_path = path.rstrip("/")

        if "admin/update-balance" in request_path:
            target_user = str(data.get("user_id"))
            amount = float(data.get("amount", 0))
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (target_user,))
            row = cursor.fetchone()
            if row:
                new_balance = max(0.0, row[0] + amount)
                cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_user))
                conn.commit()
                response = {"success": True, "new_balance": new_balance}
            else:
                response = {"success": False, "error": "User not found"}
            conn.close()
            self.send_json(200, json.dumps(response).encode("utf-8"))
            return

        if "admin/create-gift-link" in request_path:
            amount = float(data.get("amount", 0))
            max_uses = int(data.get("max_uses", 1))
            code = uuid.uuid4().hex[:8]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gift_links (code, amount, max_uses, current_uses) VALUES (?, ?, ?, 0)", 
                           (code, amount, max_uses))
            conn.commit()
            conn.close()
            response = {"success": True, "code": code, "amount": amount, "max_uses": max_uses}
            self.send_json(200, json.dumps(response).encode("utf-8"))
            return

        if "user/claim-gift" in request_path:
            user_id = str(data.get("user_id"))
            code = str(data.get("code"))
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT amount, max_uses, current_uses FROM gift_links WHERE code = ?", (code,))
            gift = cursor.fetchone()
            if not gift:
                conn.close()
                self.send_json(200, json.dumps({"success": False, "error": "الرابط غير صالح"}).encode("utf-8"))
                return
            amount, max_uses, current_uses = gift
            cursor.execute("SELECT * FROM user_gifts WHERE user_id = ? AND code = ?", (user_id, code))
            if cursor.fetchone():
                conn.close()
                self.send_json(200, json.dumps({"success": False, "error": "استلمت الهدية مسبقاً"}).encode("utf-8"))
                return
            if current_uses >= max_uses:
                conn.close()
                self.send_json(200, json.dumps({"success": False, "error": "نفدت استخدامات الهدية"}).encode("utf-8"))
                return
            get_or_create_user(user_id)
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            cursor.execute("UPDATE gift_links SET current_uses = current_uses + 1 WHERE code = ?", (code,))
            cursor.execute("INSERT INTO user_gifts (user_id, code) VALUES (?, ?)", (user_id, code))
            conn.commit()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            new_balance = cursor.fetchone()[0]
            conn.close()
            self.send_json(200, json.dumps({"success": True, "amount": amount, "new_balance": new_balance}).encode("utf-8"))
            return

        self.send_json(200, b'{"success": true, "status": "ok"}')

    def send_json(self, status, data_bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data_bytes)))
        self.end_headers()
        self.wfile.write(data_bytes)

def run_server():
    port = int(os.environ.get("PORT", 8001))
    print(f"🚀 Server running on port {port}...")
    ThreadingHTTPServer(("0.0.0.0", port), RocketHandler).serve_forever()


# --- تشغيل بوت التليجرام تلقائياً ---
def run_telegram_bot():
    print("🤖 Telegram Bot started...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=35).json()
            if res.get("ok"):
                for update in res.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue
                    
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    text = message.get("text", "")

                    # إنشاء حساب ومنح 30 تون عند أول تفاعل
                    get_or_create_user(user_id)

                    # معالجة أمر /start
                    if text.startswith("/start"):
                        parts = text.split()
                        if len(parts) > 1 and parts[1].startswith("gift_"):
                            code = parts[1].replace("gift_", "")
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("SELECT amount, max_uses, current_uses FROM gift_links WHERE code = ?", (code,))
                            gift = cursor.fetchone()
                            
                            gift_msg = "❌ رابط الهدية غير صالح أو انتهى."
                            if gift:
                                amt, max_u, cur_u = gift
                                cursor.execute("SELECT * FROM user_gifts WHERE user_id = ? AND code = ?", (str(user_id), code))
                                if cursor.fetchone():
                                    gift_msg = "⚠️ لقد قمت باستلام هذه الهدية مسبقاً!"
                                elif cur_u >= max_u:
                                    gift_msg = "⚠️ عذراً، نفدت عدد استخدامات هذه الهدية!"
                                else:
                                    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, str(user_id)))
                                    cursor.execute("UPDATE gift_links SET current_uses = current_uses + 1 WHERE code = ?", (code,))
                                    cursor.execute("INSERT INTO user_gifts (user_id, code) VALUES (?, ?)", (str(user_id), code))
                                    conn.commit()
                                    gift_msg = f"🎉 مبروك! تم إضافة {amt} تون إلى رصيدك بنجاح!"
                            conn.close()

                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                          json={"chat_id": chat_id, "text": gift_msg})

                        # الرسالة الترحيبية مع زر الدخول للعبة
                        payload = {
                            "chat_id": chat_id,
                            "text": "مرحباً بك! يمكنك الدخول للعبة والاستمتاع بالرصيد الافتتاحي (30 TON):",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [{"text": "🎮 يمكنك الدخول للعب", "web_app": {"url": WEBAPP_URL}}]
                                ]
                            }
                        }
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json=payload)

                    # أوامر لوحة تحكم المالك (فقط لايدي المالك 6915929098)
                    elif user_id == ADMIN_USER_ID:
                        if text.startswith("/add"):
                            parts = text.split()
                            if len(parts) == 3:
                                target = parts[1]
                                amt = float(parts[2])
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, target))
                                conn.commit()
                                conn.close()
                                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                              json={"chat_id": chat_id, "text": f"✅ تمت إضافة {amt} تون بنجاح للمستخدم {target}"})
                            else:
                                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                              json={"chat_id": chat_id, "text": "⚠️ الاستخدام الصحيح: /add [user_id] [amount]"})

                        elif text.startswith("/gift"):
                            parts = text.split()
                            if len(parts) == 3:
                                amt = float(parts[1])
                                uses = int(parts[2])
                                code = uuid.uuid4().hex[:8]
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO gift_links (code, amount, max_uses, current_uses) VALUES (?, ?, ?, 0)", 
                                               (code, amt, uses))
                                conn.commit()
                                conn.close()
                                # استبدل YourBotUsername بمعرف بوتك الحقيقي
                                gift_link = f"https://t.me/YourBotUsername?start=gift_{code}"
                                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                              json={"chat_id": chat_id, "text": f"🎁 تم إنشاء رابط الهدية بنجاح!\nالقيمة: {amt} تون\nالعدد: {uses} أشخاص\nالرابط:\n{gift_link}"})
                            else:
                                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                                              json={"chat_id": chat_id, "text": "⚠️ الاستخدام الصحيح: /gift [amount] [max_uses]"})

        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    # تشغيل السيرفر وبوت التليجرام معاً
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    run_telegram_bot()