"""
批量采集抖音爆款视频数据

首次使用:
  python3 batch_collect.py --login
  → 扫码登录，Cookie自动保存

日常采集:
  python3 batch_collect.py                      # 单次采集
  python3 batch_collect.py --mode loop --hours 72  # 持续3天
  python3 batch_collect.py --mode past --days 30    # 回溯30天
"""
import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crawlers.douyin.web.web_crawler import DouyinWebCrawler

crawler = DouyinWebCrawler()
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "douyin_cookies.json")
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "playwright_profile")

CATEGORIES = [
    "搞笑", "美食", "旅游", "音乐", "舞蹈",
    "科技", "时尚", "宠物", "体育", "游戏",
    "美妆", "影视", "生活", "情感", "知识",
]


# =========== 登录 ===========

def login_and_save_cookies():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("请先安装: pip3 install playwright")
        return False

    print("=" * 60)
    print("📱 请在浏览器窗口中扫码登录抖音")
    print("   登录成功后，回到终端按 Enter 键")
    print("=" * 60)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto("https://www.douyin.com", timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)

        try:
            input("\n⏳ 登录完成后按 Enter...")
        except (EOFError, KeyboardInterrupt):
            pass

        cookies = context.cookies()
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ Cookie已保存 ({len(cookies)} 条)")
        context.close()

# =========== 数据提取 ===========

def extract_video_info(aweme: dict, source: str = "") -> dict:
    stats = aweme.get("statistics", {})
    author = aweme.get("author", {})
    video = aweme.get("video", {}) or {}
    dur = video.get("duration", 0) / 1000 if video.get("duration") else 0

    tags = [
        t["hashtag_name"]
        for t in (aweme.get("text_extra") or [])
        if t.get("hashtag_name")
    ]

    ct = aweme.get("create_time", 0)
    cdate = ""
    if ct:
        try:
            cdate = datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

    return {
        "aweme_id": str(aweme.get("aweme_id", "")),
        "desc": (aweme.get("desc", "") or "")[:150].replace("\n", " "),
        "create_time": ct,
        "create_date": cdate,
        "duration_sec": round(dur, 1),
        "digg_count": stats.get("digg_count", 0),
        "comment_count": stats.get("comment_count", 0),
        "share_count": stats.get("share_count", 0),
        "play_count": stats.get("play_count", 0),
        "collect_count": stats.get("collect_count", 0),
        "author_uid": str(author.get("uid", "")),
        "author_nickname": author.get("nickname", ""),
        "author_follower_count": author.get("follower_count", 0),
        "hashtags": ";".join(tags),
        "is_ads": aweme.get("is_ads", False),
        "source": source,
        "collect_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# =========== 核心采集 ===========

def scrape_with_browser(keywords: list[str], max_per_term: int = 3,
                         headless: bool = False) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    saved = None
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE) as f:
            saved = json.load(f)
    if not saved:
        print("  ⚠ 请先登录: python3 batch_collect.py --login")
        return []

    all_videos = []
    seen = set()

    print(f"  [Browser] 启动 (关键词: {len(keywords)})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=headless)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        ctx.add_cookies(saved)
        page = ctx.new_page()

        # 预热session
        try:
            page.goto("https://www.douyin.com", timeout=15000, wait_until="domcontentloaded")
            time.sleep(2)
        except:
            pass

        for i, kw in enumerate(keywords):
            print(f"    [{i+1}/{len(keywords)}] {kw}")

            try:
                # 步骤1: 打开搜索页，从DOM提取视频ID
                page.goto(
                    f"https://www.douyin.com/search/{kw}?type=video",
                    timeout=20000, wait_until="domcontentloaded"
                )
                time.sleep(4)

                vids = page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a[href*="/video/"]');
                        const ids = new Set();
                        links.forEach(a => {
                            const m = a.href.match(/video\\/(\\d+)/);
                            if (m) ids.add(m[1]);
                        });
                        return [...ids];
                    }
                """)
                vids = [v for v in vids if v not in seen]
                print(f"      从页面提取到 {len(vids)} 个视频ID")

                # 步骤2: 逐个调用视频详情API (浏览器JS fetch)
                for vid in vids[:max_per_term]:
                    if vid in seen:
                        continue
                    seen.add(vid)

                    detail = page.evaluate("""
                        async (vid) => {
                            try {
                                const url = `https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=${vid}&aid=6383`;
                                const resp = await fetch(url, {credentials:'include'});
                                const data = await resp.json();
                                return JSON.stringify(data);
                            } catch(e) { return '{}'; }
                        }
                    """, vid)
                    d = json.loads(detail)
                    if d.get("aweme_detail"):
                        info = extract_video_info(
                            d["aweme_detail"], source=f"search:{kw}"
                        )
                        all_videos.append(info)
                        print(
                            f"      👍{info['digg_count']:,} "
                            f"💬{info['comment_count']:,} "
                            f"⏱{info['duration_sec']}s "
                            f"| {info['desc'][:35]}"
                        )

            except Exception as e:
                print(f"      ⚠ {e}")
                continue

        ctx.close()

    print(f"  [Browser] 完成: {len(all_videos)} 条")
    return all_videos


# =========== 热榜 ===========

async def get_hot_topics() -> list[str]:
    try:
        r = await crawler.fetch_hot_search_result()
        wl = r.get("data", {}).get("word_list", []) or r.get("word_list", [])
        return [item.get("word", "") for item in wl[:30] if item.get("word")]
    except:
        return []


# =========== CSV ===========

def save_csv(videos: list[dict], filename: str):
    if not videos:
        print("⚠ 没有数据")
        return
    seen = set()
    unique = [v for v in videos if not (v["aweme_id"] in seen or seen.add(v["aweme_id"]))]
    print(f"  去重: {len(unique)} 条")
    if unique:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(unique[0].keys()))
            w.writeheader()
            w.writerows(unique)
        print(f"  ✅ {filename}")


# =========== 模式 ===========

async def run_once(output_csv: str = None, headless: bool = False):
    if not output_csv:
        output_csv = f"douyin_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print("=" * 60)
    print(f"🎬 抖音视频采集 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    topics = await get_hot_topics()
    keywords = (topics[:5] if topics else []) + CATEGORIES[:5]
    print(f"\n📌 {len(keywords)} 个关键词\n")
    videos = await asyncio.to_thread(scrape_with_browser, keywords, 3, headless)
    save_csv(videos, output_csv)
    return output_csv


async def run_past(days: int, output_csv: str = None, headless: bool = False):
    if not output_csv:
        output_csv = f"douyin_videos_past{days}d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print("=" * 60)
    print(f"🎬 抖音视频采集 | 回溯 {days} 天")
    print("=" * 60)
    keywords = CATEGORIES * 3
    print(f"\n📌 {len(keywords)} 个关键词")
    videos = await asyncio.to_thread(scrape_with_browser, keywords, 3, headless)
    if days and videos:
        cutoff = datetime.now().timestamp() - days * 86400
        videos = [v for v in videos if v.get("create_time", 0) >= cutoff]
        print(f"  时间筛选: {len(videos)} 条")
    save_csv(videos, output_csv)
    return output_csv


async def run_loop(total_h: float, interval_h: float):
    print(f"🔄 持续采集 | 总{total_h}h 间隔{interval_h}h")
    end_t = time.time() + total_h * 3600
    n = 0
    while time.time() < end_t:
        n += 1
        print(f"\n--- 第 {n} 次 ---")
        await run_once()
        if time.time() >= end_t:
            break
        print(f"⏳ 等待 {interval_h}h...")
        await asyncio.sleep(interval_h * 3600)
    print(f"\n✅ {n} 次完成")


def main():
    parser = argparse.ArgumentParser(description="抖音爆款视频批量采集")
    parser.add_argument("--login", action="store_true", help="扫码登录保存Cookie")
    parser.add_argument("--mode", choices=["once", "loop", "past"], default="once")
    parser.add_argument("--hours", type=float, default=72)
    parser.add_argument("--interval", type=float, default=6)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    if args.login:
        login_and_save_cookies()
        return

    if args.mode == "loop":
        asyncio.run(run_loop(args.hours, args.interval))
    elif args.mode == "past":
        asyncio.run(run_past(args.days, args.output, args.headless))
    else:
        asyncio.run(run_once(args.output, args.headless))


if __name__ == "__main__":
    main()
