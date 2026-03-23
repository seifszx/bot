import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== التوكن =====================
TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"

# ===================== مجلد للصور =====================
if not os.path.exists("screenshots"):
    os.makedirs("screenshots")

async def take_screenshot(page, name, update, context):
    """التقاط لقطة شاشة وإرسالها للمستخدم"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/{name}_{timestamp}.png"
    await page.screenshot(path=filename, full_page=True)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(filename, 'rb'))
    return filename

async def automate_google_cloud(url, update, context):
    """تنفيذ الأتمتة الكاملة في Google Cloud"""
    
    await update.message.reply_text("🚀 جاري تشغيل المتصفح...")
    
    async with async_playwright() as p:
        # تشغيل المتصفح
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context_browser = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context_browser.new_page()
        
        # 1. فتح الرابط
        await update.message.reply_text("📂 جاري فتح الرابط...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        await take_screenshot(page, "01_opened", update, context)
        
        # 2. البحث عن زر الموافقة على الشروط (Agree / Continue)
        await update.message.reply_text("🔍 جاري البحث عن أزرار الموافقة...")
        try:
            agree_buttons = await page.query_selector_all("text=/Agree|Continue|موافق|I agree/i")
            for button in agree_buttons:
                if await button.is_visible():
                    await button.click()
                    await asyncio.sleep(2)
                    await take_screenshot(page, "02_agreed", update, context)
                    await update.message.reply_text("✅ تم الضغط على زر الموافقة")
                    break
        except Exception as e:
            await update.message.reply_text(f"⚠️ لم يتم العثور على زر موافقة: {str(e)}")
        
        # 3. البحث عن زر Create service
        await update.message.reply_text("🔍 جاري البحث عن زر Create service...")
        try:
            create_buttons = await page.query_selector_all("text=/Create service|Create/i")
            for button in create_buttons:
                if await button.is_visible():
                    await button.click()
                    await asyncio.sleep(3)
                    await take_screenshot(page, "03_clicked_create_service", update, context)
                    await update.message.reply_text("✅ تم الضغط على Create service")
                    break
        except Exception as e:
            await update.message.reply_text(f"⚠️ لم يتم العثور على Create service: {str(e)}")
        
        # 4. إدخال رابط الحاوية (Container image URL)
        await update.message.reply_text("📝 جاري إدخال رابط الحاوية...")
        try:
            # البحث عن حقل إدخال النص
            input_field = await page.query_selector("input[type='text'], input:not([type])")
            if input_field:
                await input_field.fill("docker.io/seifszx/seifszx")
                await asyncio.sleep(2)
                await take_screenshot(page, "04_filled_container", update, context)
                await update.message.reply_text("✅ تم إدخال رابط الحاوية: docker.io/seifszx/seifszx")
        except Exception as e:
            await update.message.reply_text(f"⚠️ فشل إدخال رابط الحاوية: {str(e)}")
        
        # 5. تفعيل خيار Request-based billing (إذا كان موجوداً)
        await update.message.reply_text("⚙️ جاري تفعيل خيارات الفوترة...")
        try:
            # البحث عن خيار Request-based
            request_option = await page.query_selector("text=/Request-based|Request based/i")
            if request_option:
                await request_option.click()
                await asyncio.sleep(1)
                await take_screenshot(page, "05_billing_option", update, context)
                await update.message.reply_text("✅ تم تفعيل خيار Request-based billing")
        except Exception as e:
            await update.message.reply_text(f"⚠️ لم يتم العثور على خيار الفوترة: {str(e)}")
        
        # 6. البحث عن زر Create النهائي
        await update.message.reply_text("🔍 جاري البحث عن زر Create...")
        try:
            final_create = await page.query_selector("text=/Create$/i")
            if final_create:
                await final_create.click()
                await asyncio.sleep(5)
                await take_screenshot(page, "06_final_create", update, context)
                await update.message.reply_text("✅ تم الضغط على Create")
        except Exception as e:
            await update.message.reply_text(f"⚠️ لم يتم العثور على زر Create: {str(e)}")
        
        # 7. الحصول على الرابط النهائي (Endpoint URL)
        await update.message.reply_text("🔗 جاري استخراج الرابط النهائي...")
        final_url = page.url
        await take_screenshot(page, "07_final_url", update, context)
        
        # محاولة العثور على Endpoint URL في الصفحة
        try:
            endpoint_element = await page.query_selector("text=/https:\\/\\/[a-z0-9\\-\\.]+\\.run\\.app/i")
            if endpoint_element:
                endpoint_text = await endpoint_element.text_content()
                await update.message.reply_text(f"🌐 **الرابط النهائي:**\n`{endpoint_text}`", parse_mode="Markdown")
        except:
            pass
        
        await browser.close()
        return final_url

# ===================== أوامر البوت =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /start"""
    await update.message.reply_text(
        "🤖 **مرحباً بك في بوت أتمتة Google Cloud!**\n\n"
        "أرسل لي رابط Google Cloud وسأقوم بـ:\n"
        "1️⃣ فتح الرابط\n"
        "2️⃣ الضغط على زر الموافقة\n"
        "3️⃣ الضغط على Create service\n"
        "4️⃣ إدخال رابط الحاوية\n"
        "5️⃣ تفعيل خيارات الفوترة\n"
        "6️⃣ الضغط على Create\n"
        "7️⃣ إرسال الرابط النهائي\n\n"
        "📸 **سأرسل لك لقطة شاشة بعد كل خطوة**\n\n"
        "✨ **أرسل الرابط الآن:**",
        parse_mode="Markdown"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرابط المرسل من المستخدم"""
    url = update.message.text
    
    # التأكد من أن الرابط صالح
    if not url.startswith("http"):
        await update.message.reply_text("❌ الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://")
        return
    
    await update.message.reply_text(f"✅ تم استلام الرابط:\n`{url}`\n\n⏳ جاري تنفيذ الأتمتة...", parse_mode="Markdown")
    
    try:
        final_url = await automate_google_cloud(url, update, context)
        await update.message.reply_text(
            f"✅ **تمت العملية بنجاح!**\n\n"
            f"🔗 **الرابط النهائي:**\n`{final_url}`\n\n"
            f"📸 تم إرسال لقطات الشاشة أعلاه",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ **حدث خطأ:**\n`{str(e)}`", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأمر /help"""
    await update.message.reply_text(
        "📖 **كيفية الاستخدام:**\n\n"
        "1. أرسل رابط Google Cloud الذي تريد أتمتته\n"
        "2. انتظر حتى يتم التنفيذ\n"
        "3. ستستلم لقطة شاشة بعد كل خطوة\n"
        "4. ستستلم الرابط النهائي في النهاية\n\n"
        "⚙️ **الأوامر:**\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه المساعدة",
        parse_mode="Markdown"
    )

# ===================== تشغيل البوت =====================
def main():
    app = Application.builder().token(TOKEN).build()
    
    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
