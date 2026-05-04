# 抖音爆款视频特征分析工具

基于 [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) 二次开发，研究抖音热门短视频的多维量化特征。

## 功能

- **热榜话题采集**：通过抖音热榜 API 获取实时热搜话题及热度值
- **视频数据抓取**：Playwright + 系统 Chrome 浏览器，自动搜索话题并提取视频详情（点赞、评论、分享、时长、标签、作者信息等）
- **批量采集**：单次采集 / 持续循环采集 / 回溯历史数据

## 快速开始

### 环境

- Python 3.9+
- Google Chrome 浏览器

### 安装

```bash
git clone https://github.com/nsvjeirn111/Douyin-Video-Analysis.git
cd Douyin-Video-Analysis/Douyin_TikTok_Download_API
pip3 install playwright httpx pydantic pyyaml rich aiofiles
pip3 install -r requirements.txt
```

### 使用

```bash
# 首次扫码登录（只需一次）
python3 batch_collect.py --login

# 单次采集
python3 batch_collect.py

# 回溯过去30天
python3 batch_collect.py --mode past --days 30

# 持续采集3天，每6h一次
python3 batch_collect.py --mode loop --hours 72 --interval 6
```

### 输出 CSV 字段

| 字段 | 说明 |
|------|------|
| `aweme_id` | 视频ID |
| `desc` | 视频描述 |
| `create_date` | 发布时间 |
| `duration_sec` | 时长（秒） |
| `digg_count` | 点赞数 |
| `comment_count` | 评论数 |
| `share_count` | 分享数 |
| `play_count` | 播放数 |
| `collect_count` | 收藏数 |
| `author_nickname` | 作者 |
| `author_follower_count` | 作者粉丝数 |
| `hashtags` | 话题标签 |

## 技术说明

由于抖音严格的爬虫防护（签名校验、无头浏览器检测），采用**浏览器 JS 上下文注入**方案绕过风控：

1. 热榜 API 直接调用获取热搜话题
2. 浏览器打开搜索页，从 DOM 提取视频 ID
3. 在浏览器 JS 上下文中调用 `aweme/v1/web/aweme/detail/` 接口获取详情

首次需扫码登录保存 Cookie，后续自动复用。

## 致谢

- [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)

## 许可

仅供学术研究使用。请遵守抖音平台服务条款。
