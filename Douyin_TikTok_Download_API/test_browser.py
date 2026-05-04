"""手动测试浏览器 - 不会自动退出，按Ctrl+C停止"""
from playwright.sync_api import sync_playwright
import json, time, os

with open("douyin_cookies.json") as f:
    cookies = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=False)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.add_cookies(cookies)
    page = context.new_page()

    # 访问首页
    print("打开抖音首页...")
    page.goto("https://www.douyin.com", timeout=20000)
    time.sleep(3)

    # 搜索
    print('搜索"搞笑"...')
    page.goto("https://www.douyin.com/search/搞笑?type=video", timeout=20000)
    time.sleep(5)

    # 检查页面，找视频链接
    links = page.eval_on_selector_all(
        'a[href*="/video/"]',
        'els => els.map(e => e.href).slice(0, 10)'
    )
    print(f"\n找到 {len(links)} 个视频链接:")
    for l in links:
        print(f"  {l}")

    print("\n浏览器窗口保持打开。看完按 Ctrl+C 退出。")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    context.close()
    print("已退出")
