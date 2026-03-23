import asyncio
import logging
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

PORT = int(os.environ.get("PORT", 10000))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

# شغّل health server فوراً عند import الملف
_server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
_thread = threading.Thread(target=_server.serve_forever, daemon=True)
_thread.start()
print(f"🌐 Health server يعمل على port {PORT}", flush=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبا بيك في بوت يوهان 🤖\n\nارسل رابط لبدأ عمل"
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
        await update.message.reply_text(f"❌ حدث خطأ:\n{str(e)[:200]}")

async def send_screenshot(page, update, label):
    try:
        screenshot = await page.screenshot(full_page=False)
        await update.message.reply_photo(photo=screenshot, caption=f"📸 {label}")
    except:
        pass

async def safe_click(page, selector, timeout=30000):
    try:
        el = page.locator(selector)
        await el.first.wait_for(state="visible", timeout=timeout)
        await el.first.click()
        return True
    except:
        return False

async def run_automation(url: str, update: Update) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1280,800",
            ]
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            ignore_https_errors=True,
        )
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: {} };
        """)
        page = await ctx.new_page()

        await update.message.reply_text("📡 المرحلة 1: فتح رابط Qwiklabs...")
        try:
            await page.goto(url, wait_until="commit", timeout=90000)
            await asyncio.sleep(10)
            try:
                await page.wait_for_url("*console.cloud.google.com*", timeout=45000)
                await update.message.reply_text("✅ تم تسجيل الدخول!")
            except:
                pass
        except Exception as e:
            await update.message.reply_text(f"⚠️ {str(e)[:80]}")

        await asyncio.sleep(3)
        await send_screenshot(page, update, "بعد فتح الرابط")

        await update.message.reply_text("🔐 المرحلة 2: فحص SSO...")
        try:
            for selector in ["button:has-text('أفهم ذلك')", "button:has-text('I understand')", "button:has-text('Accept')", "button:has-text('Continue')"]:
                btn = page.locator(selector)
                if await btn.count() > 0:
                    await btn.first.click()
                    await asyncio.sleep(3)
                    break
        except:
            pass

        await update.message.reply_text("📋 المرحلة 3: شروط Google Cloud...")
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
            await asyncio.sleep(2)
            checkbox = page.locator("input[type='checkbox']").first
            if await checkbox.count() > 0 and not await checkbox.is_checked():
                await checkbox.click()
                await asyncio.sleep(1)
            clicked = await safe_click(page, "button:has-text('Agree and continue')", 8000)
            if clicked:
                await asyncio.sleep(4)
                await update.message.reply_text("✅ تمت الموافقة")
            else:
                await update.message.reply_text("⏭️ تخطي...")
        except Exception as e:
            await update.message.reply_text(f"⚠️ {str(e)[:80]}")

        await update.message.reply_text("☁️ المرحلة 4: Cloud Run...")
        await page.goto("https://console.cloud.google.com/run", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)
        await send_screenshot(page, update, "صفحة Cloud Run")

        await update.message.reply_text("🔧 المرحلة 5: Create Service...")
        clicked = False
        for selector in ["button:has-text('Create service')", "a:has-text('Create service')", "button:has-text('Create')"]:
            try:
                el = page.locator(selector)
                if await el.count() > 0:
                    await el.first.click()
                    clicked = True
                    await asyncio.sleep(4)
                    await update.message.reply_text("✅ تم فتح Create Service")
                    break
            except:
                continue

        if not clicked:
            try:
                buttons = await page.locator("button").all_text_contents()
                await update.message.reply_text(f"🔍 الأزرار:\n{str(buttons)[:300]}")
            except:
                pass
            await send_screenshot(page, update, "لم أجد زر Create")
            await browser.close()
            return None

        await update.message.reply_text("🐳 المرحلة 6: Container Image...")
        try:
            for selector in ["input[placeholder*='Container image URL']", "input[aria-label*='Container image']", "input[placeholder*='gcr.io']"]:
                img_input = page.locator(selector)
                if await img_input.count() > 0:
                    await img_input.first.fill("docker.io/seifszx/seifszx")
                    await asyncio.sleep(1)
                    await update.message.reply_text("✅ تم إدخال Container Image")
                    break
        except Exception as e:
            await update.message.reply_text(f"⚠️ {str(e)[:80]}")

        await update.message.reply_text("⚙️ المرحلة 7: الإعدادات...")
        try:
            await safe_click(page, "label:has-text('Instance-based')", 10000)
            await asyncio.sleep(1)
            min_input = page.locator("input[aria-label*='Minimum'], input[placeholder*='Minimum']")
            if await min_input.count() > 0:
                await min_input.first.fill("1")
            max_input = page.locator("input[aria-label*='Maximum'], input[placeholder*='Maximum']")
            if await max_input.count() > 0:
                await max_input.first.fill("16")
            await update.message.reply_text("✅ Instance-based, Min=1, Max=16")
        except Exception as e:
            await update.message.reply_text(f"⚠️ {str(e)[:80]}")

        await update.message.reply_text("🔗 المرحلة 8: Endpoint URL...")
        endpoint_url = ""
        try:
            for selector in ["text=.run.app", "[aria-label*='Endpoint']"]:
                el = page.locator(selector)
                if await el.count() > 0:
                    endpoint_url = (await el.first.inner_text()).strip()
                    if ".run.app" in endpoint_url:
                        break
        except:
            pass

        await update.message.reply_text("🚀 المرحلة 9: Create...")
        try:
            await safe_click(page, "button:has-text('Create')", 10000)
            await asyncio.sleep(8)
            await update.message.reply_text("✅ تم!")
        except Exception as e:
            await update.message.reply_text(f"⚠️ {str(e)[:80]}")

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
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("🤖 بوت يوهان يعمل...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()

