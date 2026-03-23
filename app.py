import asyncio
import threading
import logging
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/")
def home():
    return "🤖 بوت يوهان - Web Service يعمل!", 200

@app.route("/run", methods=["POST"])
def run_automation():
    data = request.json
    url = data.get("url", "")
    if not url.startswith("http"):
        return jsonify({"error": "رابط غير صحيح"}), 400

    # شغّل الأتمتة في thread منفصل
    result = {"steps": [], "endpoint_url": ""}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(automate(url))
    except Exception as e:
        result["error"] = str(e)[:300]
    finally:
        loop.close()

    return jsonify(result)

async def automate(url: str) -> dict:
    steps = []
    endpoint_url = ""

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

        # المرحلة 1
        steps.append("📡 المرحلة 1: فتح رابط Qwiklabs...")
        try:
            await page.goto(url, wait_until="commit", timeout=90000)
            await asyncio.sleep(10)
            try:
                await page.wait_for_url("*console.cloud.google.com*", timeout=45000)
                steps.append("✅ تم تسجيل الدخول!")
            except:
                steps.append("⚠️ انتظار تسجيل الدخول انتهى")
        except Exception as e:
            steps.append(f"⚠️ خطأ: {str(e)[:80]}")

        # المرحلة 2: SSO
        steps.append("🔐 المرحلة 2: فحص SSO...")
        try:
            for selector in ["button:has-text('أفهم ذلك')", "button:has-text('I understand')", "button:has-text('Accept')", "button:has-text('Continue')"]:
                btn = page.locator(selector)
                if await btn.count() > 0:
                    await btn.first.click()
                    await asyncio.sleep(3)
                    steps.append("✅ تم الضغط على زر الموافقة")
                    break
        except:
            pass

        # المرحلة 3: شروط Cloud
        steps.append("📋 المرحلة 3: شروط Google Cloud...")
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
            await asyncio.sleep(2)
            checkbox = page.locator("input[type='checkbox']").first
            if await checkbox.count() > 0 and not await checkbox.is_checked():
                await checkbox.click()
                await asyncio.sleep(1)
            agree = page.locator("button:has-text('Agree and continue')")
            if await agree.count() > 0:
                await agree.first.click()
                await asyncio.sleep(4)
                steps.append("✅ تمت الموافقة على شروط Google Cloud")
            else:
                steps.append("⏭️ لا توجد شروط")
        except Exception as e:
            steps.append(f"⚠️ {str(e)[:80]}")

        # المرحلة 4: Cloud Run
        steps.append("☁️ المرحلة 4: الذهاب إلى Cloud Run...")
        await page.goto("https://console.cloud.google.com/run", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)
        steps.append(f"🔗 URL الحالي: {page.url[:100]}")

        # المرحلة 5: Create Service
        steps.append("🔧 المرحلة 5: Create Service...")
        clicked = False
        for selector in ["button:has-text('Create service')", "a:has-text('Create service')", "button:has-text('Create')"]:
            try:
                el = page.locator(selector)
                if await el.count() > 0:
                    await el.first.click()
                    clicked = True
                    await asyncio.sleep(4)
                    steps.append("✅ تم فتح Create Service")
                    break
            except:
                continue

        if not clicked:
            try:
                buttons = await page.locator("button").all_text_contents()
                steps.append(f"🔍 الأزرار الموجودة: {str(buttons)[:200]}")
            except:
                pass
            await browser.close()
            return {"steps": steps, "endpoint_url": "", "error": "لم أجد زر Create Service"}

        # المرحلة 6: Container Image
        steps.append("🐳 المرحلة 6: Container Image...")
        try:
            for selector in ["input[placeholder*='Container image URL']", "input[aria-label*='Container image']", "input[placeholder*='gcr.io']"]:
                img_input = page.locator(selector)
                if await img_input.count() > 0:
                    await img_input.first.fill("docker.io/seifszx/seifszx")
                    await asyncio.sleep(1)
                    steps.append("✅ تم إدخال Container Image")
                    break
        except Exception as e:
            steps.append(f"⚠️ {str(e)[:80]}")

        # المرحلة 7: الإعدادات
        steps.append("⚙️ المرحلة 7: الإعدادات...")
        try:
            instance = page.locator("label:has-text('Instance-based')")
            if await instance.count() > 0:
                await instance.first.click()
                await asyncio.sleep(1)
            min_input = page.locator("input[aria-label*='Minimum'], input[placeholder*='Minimum']")
            if await min_input.count() > 0:
                await min_input.first.fill("1")
            max_input = page.locator("input[aria-label*='Maximum'], input[placeholder*='Maximum']")
            if await max_input.count() > 0:
                await max_input.first.fill("16")
            steps.append("✅ Instance-based, Min=1, Max=16")
        except Exception as e:
            steps.append(f"⚠️ {str(e)[:80]}")

        # المرحلة 8: Endpoint URL
        steps.append("🔗 المرحلة 8: Endpoint URL...")
        try:
            for selector in ["text=.run.app", "[aria-label*='Endpoint']"]:
                el = page.locator(selector)
                if await el.count() > 0:
                    endpoint_url = (await el.first.inner_text()).strip()
                    if ".run.app" in endpoint_url:
                        steps.append(f"✅ URL: {endpoint_url}")
                        break
        except:
            pass

        # المرحلة 9: Create
        steps.append("🚀 المرحلة 9: الضغط على Create...")
        try:
            create_btn = page.locator("button:has-text('Create')").last
            await create_btn.click()
            await asyncio.sleep(8)
            steps.append("✅ تم الضغط على Create!")
        except Exception as e:
            steps.append(f"⚠️ {str(e)[:80]}")

        # محاولة أخيرة للـ URL
        if not endpoint_url:
            try:
                await asyncio.sleep(5)
                url_el = page.locator("a[href*='.run.app']")
                if await url_el.count() > 0:
                    endpoint_url = await url_el.first.get_attribute("href")
                    steps.append(f"✅ URL: {endpoint_url}")
            except:
                pass

        await browser.close()

    return {"steps": steps, "endpoint_url": endpoint_url}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server يعمل على port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
