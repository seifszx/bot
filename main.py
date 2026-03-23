import asyncio
import logging
import subprocess
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

def install_playwright():
    print("🔧 جاري تحميل متصفح Firefox...")
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "firefox"],
        check=True
    )
    print("✅ تم تثبيت المتصفح بنجاح!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 مرحباً!\n\n"
        "أرسل لي رابط Qwiklabs وسأقوم بـ:\n"
        "1️⃣ فتح الرابط تلقائياً\n"
        "2️⃣ الموافقة على شروط Google\n"
        "3️⃣ إنشاء Cloud Run Service\n"
        "4️⃣ إرسال الـ Endpoint URL إليك\n\n"
        "📎 أرسل الرابط الآن!"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ يرجى إرسال رابط صحيح يبدأ بـ http")
        return

    await update.message.reply_text("🚀 بدأت العملية... انتظر!")

    try:
        endpoint_url = await run_automation(url, update)
        if endpoint_url:
            await update.message.reply_text(
                f"✅ تم بنجاح!\n\n🔗 Endpoint URL:\n`{endpoint_url}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ انتهت العملية لكن لم أتمكن من استخراج الـ URL.")
    except Exception as e:
        logger.error(f"Error: {e}")
        err_text = str(e)[:200]
        await update.message.reply_text(f"❌ حدث خطأ:\n{err_text}")

async def run_automation(url: str, update: Update) -> str:
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await ctx.new_page()

        # ── المرحلة 1 ──
        await update.message.reply_text("📡 المرحلة 1: فتح رابط Qwiklabs...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        # ── المرحلة 2: Google SSO ──
        await update.message.reply_text("🔐 المرحلة 2: الموافقة على Google SSO...")
        try:
            accept_btn = page.locator("button:has-text('أفهم ذلك'), button:has-text('I understand'), button:has-text('Accept')")
            if await accept_btn.count() > 0:
                await accept_btn.first.click()
                await asyncio.sleep(2)
                await update.message.reply_text("✅ تمت الموافقة على Google SSO")
            else:
                await update.message.reply_text("⏭️ لا توجد صفحة SSO، تخطي...")
        except Exception as e:
            await update.message.reply_text(f"⚠️ تخطي SSO: {str(e)[:80]}")

        # ── المرحلة 3: شروط Google Cloud ──
        await update.message.reply_text("📋 المرحلة 3: الموافقة على شروط Google Cloud...")
        try:
            await page.wait_for_selector("text=I agree to the Google Cloud Platform", timeout=15000)
            checkbox = page.locator("input[type='checkbox']").first
            if not await checkbox.is_checked():
                await checkbox.click()
                await asyncio.sleep(1)
            agree_btn = page.locator("button:has-text('Agree and continue')")
            if await agree_btn.count() > 0:
                await agree_btn.first.click()
                await asyncio.sleep(3)
                await update.message.reply_text("✅ تمت الموافقة على شروط Google Cloud")
        except Exception as e:
            await update.message.reply_text(f"⚠️ تخطي شروط Cloud: {str(e)[:80]}")

        # ── المرحلة 4: Cloud Run ──
        await update.message.reply_text("☁️ المرحلة 4: الذهاب إلى Cloud Run...")
        await page.goto("https://console.cloud.google.com/run", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # ── المرحلة 5: Create Service ──
        await update.message.reply_text("🔧 المرحلة 5: إنشاء Cloud Run Service...")
        try:
            create_btn = page.locator("button:has-text('Create service'), a:has-text('Create service')")
            await create_btn.first.wait_for(timeout=15000)
            await create_btn.first.click()
            await asyncio.sleep(3)
            await update.message.reply_text("✅ تم فتح نافذة Create Service")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في Create Service: {str(e)[:80]}")
            await browser.close()
            return None

        # ── المرحلة 6: Container Image ──
        await update.message.reply_text("🐳 المرحلة 6: إدخال Container Image...")
        try:
            img_input = page.locator("input[placeholder*='Container image URL'], input[aria-label*='Container image']")
            await img_input.first.wait_for(timeout=15000)
            await img_input.first.fill("docker.io/seifszx/seifszx")
            await asyncio.sleep(1)
            await update.message.reply_text("✅ تم إدخال Container Image")
        except Exception as e:
            await update.message.reply_text(f"⚠️ مشكلة في Container URL: {str(e)[:80]}")

        # ── المرحلة 7: الإعدادات ──
        await update.message.reply_text("⚙️ المرحلة 7: ضبط الإعدادات...")
        try:
            instance_radio = page.locator("label:has-text('Instance-based')")
            if await instance_radio.count() > 0:
                await instance_radio.first.click()
                await asyncio.sleep(1)
            min_input = page.locator("input[aria-label*='Minimum'], input[placeholder*='Minimum']")
            if await min_input.count() > 0:
                await min_input.first.fill("1")
                await asyncio.sleep(0.5)
            max_input = page.locator("input[aria-label*='Maximum'], input[placeholder*='Maximum']")
            if await max_input.count() > 0:
                await max_input.first.fill("16")
                await asyncio.sleep(0.5)
            await update.message.reply_text("✅ تم ضبط الإعدادات: Instance-based, Min=1, Max=16")
        except Exception as e:
            await update.message.reply_text(f"⚠️ مشكلة في الإعدادات: {str(e)[:80]}")

        # ── المرحلة 8: استخراج URL ──
        await update.message.reply_text("🔗 المرحلة 8: استخراج Endpoint URL...")
        endpoint_url = ""
        try:
            endpoint_el = page.locator("text=.run.app")
            if await endpoint_el.count() > 0:
                endpoint_url = (await endpoint_el.first.inner_text()).strip()
        except:
            pass

        # ── المرحلة 9: Create ──
        await update.message.reply_text("🚀 المرحلة 9: الضغط على Create...")
        try:
            final_create = page.locator("button:has-text('Create')").last
            await final_create.click()
            await asyncio.sleep(5)
            await update.message.reply_text("✅ تم الضغط على Create! السيرفس قيد الإنشاء...")
        except Exception as e:
            await update.message.reply_text(f"⚠️ مشكلة في Create: {str(e)[:80]}")

        if not endpoint_url:
            try:
                await asyncio.sleep(5)
                url_el = page.locator("a[href*='.run.app']")
                if await url_el.count() > 0:
                    endpoint_url = await url_el.first.get_attribute("href")
            except:
                pass

        await browser.close()
        return endpoint_url

def main():
    install_playwright()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
