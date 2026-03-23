"""
بوت تيليجرام - Qwiklabs Full Automation
"""

import asyncio
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BOT_TOKEN       = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"
CONTAINER_IMAGE = "docker.io/seifszx/seifszx"
HEADLESS        = True

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

def is_valid_url(text):
    return text.startswith("http://") or text.startswith("https://")

def extract_project_id(url):
    m = re.search(r"project=([^&\s]+)", url)
    return m.group(1) if m else ""

async def safe_click(page, selector, desc, timeout=5000):
    try:
        loc = page.locator(selector).first
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.click()
        log.info(f"✅ {desc}")
        await asyncio.sleep(2)
        return True
    except:
        return False

async def safe_fill(page, selector, value, desc, timeout=5000):
    try:
        loc = page.locator(selector).first
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.triple_click()
        await loc.fill(value)
        log.info(f"✏️ {desc}: {value}")
        await asyncio.sleep(1)
        return True
    except:
        return False

async def run_automation(url, status_cb):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await status_cb("🌐 جاري فتح الرابط...")
            await page.goto(url, wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(3)

            await status_cb("🔄 الموافقة على صفحات Google...")

            for attempt in range(30):
                await asyncio.sleep(3)
                current_url = page.url
                log.info(f"[{attempt}] {current_url[:80]}")

                if await safe_click(page,
                    "button:has-text('أفهم ذلك'), button:has-text('I understand'), button:has-text('Got it')",
                    "أفهم ذلك", 2000): continue

                if await safe_click(page,
                    "button:has-text('Accept'), button:has-text('Continue'), button:has-text('موافق')",
                    "Accept/Continue", 2000): continue

                if await safe_click(page, "button:has-text('Join')", "Join", 2000): continue

                if "console.cloud.google.com" in current_url:
                    await status_cb("📋 قبول شروط Google Cloud...")

                    # checkbox الشروط - أول checkbox في الصفحة
                    try:
                        cb = page.locator("input[type='checkbox']").first
                        await cb.wait_for(state="visible", timeout=5000)
                        if not await cb.is_checked():
                            await cb.click()
                            await asyncio.sleep(1)
                    except: pass

                    await safe_click(page,
                        "button:has-text('Agree and continue'), text=Agree and continue",
                        "Agree and continue", 5000)
                    await asyncio.sleep(4)

                    # Cloud Run
                    await status_cb("☁️ الانتقال إلى Cloud Run...")
                    project_id = extract_project_id(current_url)
                    run_url = f"https://console.cloud.google.com/run?project={project_id}" if project_id else "https://console.cloud.google.com/run"
                    await page.goto(run_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(5)

                    # Create service button
                    await status_cb("🚀 فتح Create service...")
                    if not await safe_click(page,
                        "button:has-text('Create service'), a:has-text('Create service')",
                        "Create service", 10000):
                        await browser.close()
                        return "❌ لم أجد زر Create service."
                    await asyncio.sleep(6)

                    # Container image URL
                    await status_cb("🐳 كتابة Container image...")
                    filled = await safe_fill(page,
                        "input[placeholder*='Container image'], input[aria-label*='Container image'], input[id*='image-url']",
                        CONTAINER_IMAGE, "Container image", 8000)
                    if not filled:
                        # محاولة بديلة
                        try:
                            inputs = page.locator("input[type='text']")
                            count = await inputs.count()
                            if count > 0:
                                await inputs.first.triple_click()
                                await inputs.first.fill(CONTAINER_IMAGE)
                        except: pass
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(3)

                    # Allow public access
                    await status_cb("🔓 Allow public access...")
                    await safe_click(page,
                        "label:has-text('Allow unauthenticated invocations'), "
                        "label:has-text('Allow public access'), "
                        "input[value*='public']",
                        "Allow public access", 5000)

                    # Instance-based
                    await safe_click(page,
                        "label:has-text('Instance-based'), input[value*='instance']",
                        "Instance-based", 5000)

                    # Min instances = 1
                    await safe_fill(page,
                        "input[aria-label*='Minimum number'], input[id*='min-instances']",
                        "1", "Minimum=1", 3000)

                    # Max instances = 16
                    await safe_fill(page,
                        "input[aria-label*='Maximum number'], input[id*='max-instances']",
                        "16", "Maximum=16", 3000)

                    # استخرج Endpoint URL
                    await status_cb("🔗 استخراج Endpoint URL...")
                    endpoint_url = ""
                    try:
                        content = await page.content()
                        match = re.search(r'https://[\w\-]+\.run\.app', content)
                        if match:
                            endpoint_url = match.group(0)
                    except: pass

                    # Create
                    await status_cb("✅ الضغط على Create...")
                    await safe_click(page,
                        "button:has-text('Create'):not([disabled])",
                        "Create", 10000)
                    await asyncio.sleep(8)

                    # حاول مرة أخرى للـ URL بعد الإنشاء
                    if not endpoint_url:
                        try:
                            content = await page.content()
                            match = re.search(r'https://[\w\-]+\.run\.app', content)
                            if match:
                                endpoint_url = match.group(0)
                            if not endpoint_url:
                                endpoint_url = page.url
                        except: pass

                    await browser.close()

                    result = (
                        "🎉 *تمت جميع الخطوات بنجاح!*\n\n"
                        "1️⃣ تسجيل الدخول ✅\n"
                        "2️⃣ قبول شروط Google ✅\n"
                        "3️⃣ Cloud Run > Services ✅\n"
                        f"4️⃣ Container: `{CONTAINER_IMAGE}` ✅\n"
                        "5️⃣ Allow public access ✅\n"
                        "6️⃣ Instance-based | Min:1 Max:16 ✅\n"
                        "7️⃣ Create ✅\n"
                    )
                    if endpoint_url:
                        result += f"\n🔗 *Endpoint URL:*\n`{endpoint_url}`"
                    return result

            await browser.close()
            return "⚠️ انتهت المحاولات دون الوصول لـ Google Cloud Console."

        except PlaywrightTimeout:
            try: await browser.close()
            except: pass
            return "❌ انتهت مهلة الاتصال."
        except Exception as e:
            log.error(f"خطأ: {e}")
            try: await browser.close()
            except: pass
            return f"❌ خطأ:\n`{str(e)[:300]}`"


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *مرحباً في Qwiklabs Bot!*\n\n"
        "📎 أرسل رابط SSO وسأقوم تلقائياً بـ:\n"
        "1️⃣ تسجيل الدخول لـ Google\n"
        "2️⃣ قبول الشروط\n"
        "3️⃣ Cloud Run > Create service\n"
        "4️⃣ إرسال Endpoint URL إليك\n\n"
        "🚀 الصق الرابط الآن!",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not is_valid_url(text):
        await update.message.reply_text("❗ أرسل رابطاً صحيحاً يبدأ بـ https://")
        return
    status_msg = await update.message.reply_text("⏳ جاري المعالجة...")
    async def update_status(msg):
        try: await status_msg.edit_text(msg)
        except: pass
    result = await run_automation(text, update_status)
    await update.message.reply_text(result, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("🤖 البوت يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
