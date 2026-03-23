import os
import asyncio
from flask import Flask, render_template, request, jsonify
from playwright.async_api import async_playwright
import requests

app = Flask(__name__)

# توكن البوت (استبدله بتوكنك الجديد)
BOT_TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"
# معرف المستخدم الذي سيرسل له الإشعارات (استبدله بمعرفك)
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_message(message, photo_path=None):
    """إرسال رسالة أو صورة للمستخدم عبر تيليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")
    
    if photo_path and os.path.exists(photo_path):
        photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID}
            requests.post(photo_url, data=data, files=files)

async def automate_google_cloud(url, screenshot_prefix="step"):
    """تنفيذ الأتمتة وإرجاع النتائج"""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # فتح الرابط
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)
        
        # التقاط لقطة شاشة
        screenshot = f"/tmp/{screenshot_prefix}_1.png"
        await page.screenshot(path=screenshot)
        results.append(screenshot)
        
        # البحث عن زر الموافقة
        try:
            agree = await page.wait_for_selector("text=/Agree|Continue|موافق|I agree/i", timeout=5000)
            if agree:
                await agree.click()
                await page.wait_for_timeout(2000)
                screenshot2 = f"/tmp/{screenshot_prefix}_2.png"
                await page.screenshot(path=screenshot2)
                results.append(screenshot2)
        except:
            pass
        
        # البحث عن Create service
        try:
            create = await page.wait_for_selector("text=/Create service|Create/i", timeout=5000)
            if create:
                await create.click()
                await page.wait_for_timeout(3000)
                screenshot3 = f"/tmp/{screenshot_prefix}_3.png"
                await page.screenshot(path=screenshot3)
                results.append(screenshot3)
        except:
            pass
        
        # إدخال رابط الحاوية
        try:
            input_field = await page.wait_for_selector("input[type='text']", timeout=5000)
            if input_field:
                await input_field.fill("docker.io/seifszx/seifszx")
                await page.wait_for_timeout(2000)
                screenshot4 = f"/tmp/{screenshot_prefix}_4.png"
                await page.screenshot(path=screenshot4)
                results.append(screenshot4)
        except:
            pass
        
        # الحصول على الرابط النهائي
        final_url = page.url
        
        # البحث عن Endpoint URL
        try:
            endpoint = await page.query_selector("text=/https:\\/\\/[a-z0-9\\-\\.]+\\.run\\.app/i")
            if endpoint:
                endpoint_text = await endpoint.text_content()
                final_url = endpoint_text
        except:
            pass
        
        await browser.close()
        return final_url, results

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_automation():
    """تنفيذ الأتمتة"""
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "الرجاء إدخال رابط"}), 400
    
    # إرسال إشعار للمستخدم
    send_telegram_message(f"🚀 **بدء الأتمتة**\nالرابط: `{url}`")
    
    try:
        # تنفيذ الأتمتة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_url, screenshots = loop.run_until_complete(automate_google_cloud(url))
        
        # إرسال النتيجة للمستخدم
        message = f"✅ **تمت الأتمتة بنجاح!**\n\n🔗 **الرابط النهائي:**\n`{final_url}`"
        send_telegram_message(message)
        
        # إرسال لقطات الشاشة
        for i, screenshot in enumerate(screenshots):
            send_telegram_message(f"📸 **لقطة {i+1}**", screenshot)
        
        return jsonify({
            "success": True,
            "final_url": final_url,
            "message": "تم التنفيذ بنجاح"
        })
        
    except Exception as e:
        error_msg = f"❌ **حدث خطأ:**\n`{str(e)}`"
        send_telegram_message(error_msg)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
