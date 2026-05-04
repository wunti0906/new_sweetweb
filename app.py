import os
import json
import firebase_admin
from flask import Flask, render_template, send_from_directory
from firebase_admin import credentials, messaging

# 1. 初始化 Flask
app = Flask(__name__)

# 2. 初始化 Firebase Admin SDK (相容本機與 Vercel)
JSON_FILE_NAME = "sweetwebnotification-firebase-adminsdk-fbsvc-4196e8709b.json"

if not firebase_admin._apps:
    try:
        # 優先權 1：檢查本機是否有 JSON 檔案 (用於 127.0.0.1 測試)
        if os.path.exists(JSON_FILE_NAME):
            cred = credentials.Certificate(JSON_FILE_NAME)
            firebase_admin.initialize_app(cred)
            print(f"--- 成功：已透過實體檔案 {JSON_FILE_NAME} 初始化 ---")
        
        # 優先權 2：檢查是否有 Vercel 環境變數 (用於雲端部署)
        else:
            cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("--- 成功：已透過 Vercel 環境變數初始化 ---")
            else:
                print("--- 錯誤：找不到任何 Firebase 憑證來源 ---")
    except Exception as e:
        print(f"Firebase 初始化發生異常: {e}")

# 3. 發送通知的工具函數
def send_fcm_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='default',  # 必須與 Android 端的 Channel ID 一致
                click_action='FLUTTER_NOTIFICATION_CLICK'
            )
        ),
        token=token
    )
    return messaging.send(message)

# 4. 路由設定
@app.route('/')
def index():
    # 這樣 Flask 就會去 templates 資料夾找你的 index.html
    return render_template('index.html')

@app.route('/test_push')
def test_push():
    # 這裡請貼上你在 Logcat 抓到的最新 Token
    target_token = "fkO5PcrjTpiM6ZcenslPRS:APA91bFQV8UjIYWgbVmPtiFCAh5dx0MRv3E2ZaG7PwNYuTvob2gcTRXwta_sJb_3Cv5etIpNvt3YbvpTEyDnsvG8_LK01hkKhJc3MzZBwn8nig4NtnFp1uo"
    
    try:
        response = send_fcm_notification(
            target_token, 
            "系統測試", 
            "國王/女王萬歲！這是來自 Flask 的推播。"
        )
        return f"發送成功！回傳 ID: {response}"
    except Exception as e:
        return f"發送失敗，原因：{str(e)}"

# PWA 支援路由
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('templates', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('templates', 'sw.js')

# 在 app.py 加入此路由@app.route('/submit_task_notification', methods=['POST'])
def send_notification():
    data = request.get_json()
    sender_id = data.get('sender_id')
    item_name = data.get('item_name')
    
    # 如果發送者是 1，通知對象就是 2，反之亦然
    target_user = "2" if str(sender_id) == "1" else "1"
    
    # 從 Firestore 的 tokens 集合抓取目標的 Token
    token_doc = db.collection('tokens').document(f'user_{target_user}').get()
    
    if token_doc.exists:
        registration_token = token_doc.to_dict().get('fcm_token')
        
        # 這裡執行 Firebase Admin SDK 的發送邏輯
        message = messaging.Message(
            notification=messaging.Notification(
                title='收到新的提案！',
                body=f'對方提交了：{item_name}',
            ),
            token=registration_token,
        )
        response = messaging.send(message)
        return jsonify({"success": True, "msg": "通知已發送"})
    
    return jsonify({"success": False, "msg": "找不到目標 Token"})

if __name__ == '__main__':
    # 本機開發建議開啟 debug 模式
    app.run(debug=True, port=5000)