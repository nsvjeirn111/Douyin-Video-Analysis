# 抖音爆款视频特征分析工具


## 项目简介

研究抖音爆款短视频的多维量化特征，包括视频时长、内容话题、互动指标（点赞/评论/分享/播放量）、作者特征等，为创作者提供数据驱动的选题和制作建议。

## 数据采集

基于 [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) 二次开发，新增功能：

- **热榜话题采集**：通过抖音热榜 API 获取实时热搜话题及热度值
- **视频数据抓取**：通过 Playwright + 系统 Chrome 浏览器，自动搜索话题并提取视频详情（点赞、评论、分享、时长、标签、作者信息等）
- **批量采集模式**：支持单次采集、持续循环采集、回溯历史数据

## 快速开始

### 环境要求

- Python 3.9+
- Google Chrome 浏览器
- Playwright

### 安装

```bash
# 克隆仓库
git clone https://github.com/nsvjeirn111/Douyin-Video-Analysis.git
cd Douyin-Video-Analysis

# 安装依赖
pip3 install playwright httpx pydantic pyyaml rich aiofiles tenacity gmssl
pip3 install -r Douyin_TikTok_Download_API/requirements.txt
```

### 使用

```bash
# 1. 首次使用：扫码登录抖音（只需一次）
python3 batch_collect.py --login

# 2. 日常采集
python3 batch_collect.py                       # 单次采集（10个话题，约30条视频）
python3 batch_collect.py --mode past --days 30  # 回溯过去30天
python3 batch_collect.py --mode loop --hours 72  # 持续3天，每6小时一次
```

### 输出

CSV 文件，每条记录为一个视频，包含字段：

| 字段 | 说明 |
|------|------|
| `aweme_id` | 视频唯一ID |
| `desc` | 视频描述/文案 |
| `create_date` | 发布时间 |
| `duration_sec` | 时长（秒） |
| `digg_count` | 点赞数 |
| `comment_count` | 评论数 |
| `share_count` | 分享数 |
| `play_count` | 播放数 |
| `collect_count` | 收藏数 |
| `author_nickname` | 作者昵称 |
| `author_follower_count` | 作者粉丝数 |
| `hashtags` | 话题标签（如 #搞笑 #美食） |
| `source` | 数据来源标注 |

## 技术说明

### 数据获取策略

由于抖音严格的反爬机制（A-Bogus/X-Bogus 签名、JSVMP 虚拟机挑战、无头浏览器检测），本项目采用**浏览器 JS 上下文注入**方案：

1. **热榜 API**（直接调用）：获取实时 50+ 个热搜话题及热度值
2. **搜索页面**（Playwright 可见浏览器）：打开 `douyin.com/search/{关键词}?type=video`，从 DOM 提取视频 ID
3. **视频详情 API**（浏览器内 fetch 注入）：在浏览器 JS 上下文中调用 `aweme/v1/web/aweme/detail/` 接口，绕过签名校验

此方案需要**登录态 Cookie**——首次运行 `--login` 扫码保存后，后续自动复用。

### 局限性

- 抖音搜索 API 直接调用受限（返回 verify_check），需通过页面 DOM 提取视频 ID
- 无法直接获取"爆款排行榜"数据——免费手段无法绕过抖音的商业化数据壁垒
- 如需高质量结构化爆款视频数据，建议使用第三方数据平台（如飞瓜数据、蝉妈妈等）

## 致谢

本项目基于以下开源项目：

- [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — 抖音/TikTok 数据爬虫框架

## 许可

仅供学术研究使用。请遵守抖音平台的服务条款和相关法律法规。
