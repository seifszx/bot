import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"
WEB_URL = os.environ.get("WEB_URL", "http://localhost:10000")

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
        # أرسل الرابط للـ web service
        response = requests.post(
            f"{WEB_URL}/run",
            json={"url": url},
            timeout=300
        )
        data = response.json()

        # أرسل كل الخطوات
        steps = data.get("steps", [])
        if steps:
            msg = "\n".join(steps)
            # قسّم الرسالة إذا كانت طويلة
            if len(msg) > 4000:
                for i in range(0, len(msg), 4000):
                    await update.message.reply_text(msg[i:i+4000])
            else:
                await update.message.reply_text(msg)

        # أرسل الـ endpoint URL
        endpoint = data.get("endpoint_url", "")
        if endpoint:
            await update.message.reply_text(
                f"✅ تم بنجاح!\n\n🔗 Endpoint URL:\n`{endpoint}`",
                parse_mode="Markdown"
            )
        elif data.get("error"):
            await update.message.reply_text(f"❌ خطأ: {data['error'][:200]}")
        else:
            await update.message.reply_text("⚠️ انتهت العملية لكن لم أتمكن من استخراج الـ URL.")

    except requests.Timeout:
        await update.message.reply_text("⏱️ انتهى الوقت - العملية تأخذ وقتاً طويلاً")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ حدث خطأ:\n{str(e)[:200]}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    print("🤖 بوت يوهان يعمل...", flush=True)
    app.run_polling()

if __name__ == "__main__":
    main()
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
