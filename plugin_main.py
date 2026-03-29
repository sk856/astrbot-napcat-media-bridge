import asyncio
import json
import re
from pathlib import Path

import aiohttp
import msgspec
import yt_dlp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from http.cookies import SimpleCookie

from .bridge_sender import send_media_via_napcat
from .douyin_ref.slides import SlidesInfo
from .douyin_ref.video import RouterData


class NapCatMediaBridgePlugin(Star):
    URL_PATTERNS = [
        r'https?://v\.douyin\.com/[^\s]+',
        r'https?://(?:www\.)?douyin\.com/[^\s]+',
        r'https?://(?:www\.)?iesdouyin\.com/[^\s]+',
        r'https?://(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item)/[^\s]+',
        r'https?://(?:www\.)?xiaohongshu\.com/explore/[A-Za-z0-9]+[^\s]*',
        r'https?://xhslink\.com/[^\s]+',
        r'https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9/?=&_.-]+',
        r'https?://m\.bilibili\.com/video/[A-Za-z0-9/?=&_.%-]+',
        r'https?://b23\.tv/[^\s]+',
        r'https?://(?:www\.)?weibo\.com/[^\s]+',
        r'https?://(?:m\.)?weibo\.cn/[^\s]+',
        r'https?://(?:www\.)?kuaishou\.com/[^\s]+',
        r'https?://v\.kuaishou\.com/[^\s]+',
        r'https?://(?:www\.)?ixigua\.com/[^\s]+',
        r'https?://(?:www\.)?youtube\.com/[^\s]+',
        r'https?://youtu\.be/[^\s]+',
        r'https?://(?:www\.)?instagram\.com/(?:reel|p)/[^\s]+',
        r'https?://(?:www\.)?x\.com/[^\s]+',
        r'https?://(?:www\.)?twitter\.com/[^\s]+',
        r'https?://(?:www\.)?tiktok\.com/[^\s]+',
        r'https?://vt\.tiktok\.com/[^\s]+',
    ]

    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context)
        self.config = config or {}
        self.download_dir = Path(self.config.get("download_dir", "/tmp/astrbot-napcat-media-bridge"))
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir = Path(self.config.get("static_dir", "/www/wwwroot/openclaw-xhs-video"))
        self.static_base_url = self.config.get("static_base_url", "http://127.0.0.1:8089/xhs-video")
        self.copy_mode = self.config.get("copy_mode", "copy")
        self.enable_auto_detect = bool(self.config.get("enable_auto_detect", True))
        self.auto_init_static_dir = bool(self.config.get("auto_init_static_dir", True))
        self.ua = self.config.get(
            "user_agent",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
        )
        self.android_ua = self.config.get(
            "android_user_agent",
            "Mozilla/5.0 (Linux; Android 14; 23013RK75C Build/UKQ1.231108.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/133.0.0.0 Mobile Safari/537.36",
        )
        self.ios_headers = {"User-Agent": self.ua, "Referer": "https://www.douyin.com/"}
        self.android_headers = {"User-Agent": self.android_ua, "Referer": "https://www.douyin.com/"}
        self._cookie_header = ""
        if self.auto_init_static_dir:
            self.ensure_static_dir()

    def ensure_static_dir(self) -> tuple[bool, str]:
        try:
            self.static_dir.mkdir(parents=True, exist_ok=True)
            return True, f"静态目录已就绪: {self.static_dir}"
        except Exception as e:
            logger.error(f"[napcat-media-bridge] ensure static dir failed: {e}")
            return False, f"静态目录创建失败: {e}"

    def build_nginx_config_example(self) -> str:
        base_path = self.static_base_url.rstrip("/")
        route = "/" + base_path.split("//", 1)[-1].split("/", 1)[-1] if "/" in base_path.split("//", 1)[-1] else "/xhs-video"
        if not route.endswith("/"):
            route = route + "/"
        return (
            "server {\n"
            "    listen 8089;\n"
            "    server_name _;\n"
            "    autoindex off;\n\n"
            f"    location {route} {{\n"
            f"        alias {self.static_dir.as_posix().rstrip('/')}/;\n"
            "        add_header Cache-Control no-store;\n"
            "        types { video/mp4 mp4; application/octet-stream bin; }\n"
            "        default_type application/octet-stream;\n"
            "    }\n"
            "}\n"
        )

    def get_init_summary(self) -> str:
        ok, msg = self.ensure_static_dir()
        lines = [msg]
        lines.append(f"static_base_url: {self.static_base_url}")
        lines.append(f"copy_mode: {self.copy_mode}")
        lines.append(f"download_dir: {self.download_dir}")
        if ok:
            lines.append("如果静态 URL 还没通，请把下面这段 Nginx 配置加上")
            lines.append(self.build_nginx_config_example())
        return "\n".join(lines)

    @filter.command("初始化静态目录", alias={"init_static", "初始化桥接"})
    async def init_static_cmd(self, event: AstrMessageEvent):
        await event.send(event.plain_result(self.get_init_summary()))

    @filter.command("检查桥接配置", alias={"check_bridge", "桥接自检"})
    async def check_bridge_cmd(self, event: AstrMessageEvent):
        static_exists = self.static_dir.exists()
        static_writable = self.static_dir.exists() and self.static_dir.is_dir()
        lines = [
            f"static_dir: {self.static_dir}",
            f"static_dir_exists: {static_exists}",
            f"static_dir_is_dir: {static_writable}",
            f"static_base_url: {self.static_base_url}",
            f"download_dir: {self.download_dir}",
            f"copy_mode: {self.copy_mode}",
            f"enable_auto_detect: {self.enable_auto_detect}",
        ]
        if not static_exists:
            lines.append("静态目录还不存在，可以执行 初始化静态目录")
        await event.send(event.plain_result("\n".join(lines)))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        if not self.enable_auto_detect:
            return
        text = self.collect_text(event).strip()
        logger.info(f"[napcat-media-bridge] incoming text: {text[:300]}")
        if not text or text.startswith("/"):
            return
        url = self.extract_supported_url(text)
        if not url:
            return
        logger.info(f"[napcat-media-bridge] matched url: {url}")
        await self._download_and_send(event, url)

    async def _download_and_send(self, event: AstrMessageEvent, url: str):
        try:
            logger.info(f"[napcat-media-bridge] start download: {url}")
            await event.send(event.plain_result("识别到视频链接，正在下载..."))
            file_path = await self.download_video(url)
            logger.info(f"[napcat-media-bridge] downloaded file: {file_path}")
            await send_media_via_napcat(
                event=event,
                local_path=str(file_path),
                static_dir=str(self.static_dir),
                static_base_url=self.static_base_url,
                copy_mode=self.copy_mode,
            )
            logger.info(f"[napcat-media-bridge] send finished: {file_path}")
        except Exception as e:
            logger.error(f"[napcat-media-bridge] 自动处理失败: {e}", exc_info=True)
            await event.send(event.plain_result(f"处理失败: {self.format_error(e)}"))

    def collect_text(self, event: AstrMessageEvent) -> str:
        parts = []
        if getattr(event, "message_str", None):
            parts.append(str(event.message_str))
        try:
            message_obj = getattr(event, "message_obj", None)
            chain = getattr(message_obj, "message", None)
            if chain:
                for comp in chain:
                    txt = getattr(comp, "text", None)
                    if txt:
                        parts.append(str(txt))
                    data = getattr(comp, "data", None)
                    if isinstance(data, dict):
                        parts.extend([str(v) for v in data.values() if isinstance(v, str)])
                    raw = getattr(comp, "raw", None)
                    if isinstance(raw, dict):
                        parts.extend([str(v) for v in raw.values() if isinstance(v, str)])
                    parts.append(str(comp))
            raw_message = getattr(message_obj, "raw_message", None)
            if raw_message:
                parts.append(str(raw_message))
        except Exception as e:
            logger.warning(f"[napcat-media-bridge] collect_text failed: {e}")
        return " ".join(p for p in parts if p)

    def extract_supported_url(self, text: str) -> str:
        for pattern in self.URL_PATTERNS:
            matched = re.search(pattern, text, flags=re.IGNORECASE)
            if matched:
                return matched.group(0).rstrip('>\"\'），。,!！？；;]}')
        return ""

    async def download_video(self, url: str) -> Path:
        url = await self.prepare_url(url)
        if any(domain in url for domain in ["douyin.com", "iesdouyin.com", "v.douyin.com"]):
            return await self.download_douyin(url)
        if any(domain in url for domain in ["bilibili.com", "b23.tv", "bili2233.cn", "bili22.cn", "bili23.cn", "bili33.cn"]):
            return await self.download_bilibili(url)
        return await self.download_with_ytdlp(url)

    async def prepare_url(self, url: str) -> str:
        if any(domain in url for domain in ["b23.tv/", "bili2233.cn/", "bili22.cn/", "bili23.cn/", "bili33.cn/"]):
            resolved = await self.resolve_bilibili_short_url(url)
            if resolved:
                url = resolved
        return self.normalize_url(url)

    def normalize_url(self, url: str) -> str:
        matched = re.search(r'(BV[0-9A-Za-z]{10})', url, flags=re.IGNORECASE)
        if matched:
            return f"https://www.bilibili.com/video/{matched.group(1)}"
        return url

    async def resolve_bilibili_short_url(self, short_url: str) -> str:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(short_url, allow_redirects=True, headers={"User-Agent": self.android_ua}, ssl=False) as resp:
                    return str(resp.url)
        except Exception as e:
            logger.warning(f"[napcat-media-bridge] resolve short bilibili url failed: {e}")
            return short_url

    def format_error(self, err: Exception) -> str:
        msg = str(err).strip() or err.__class__.__name__
        lower = msg.lower()
        if "fresh cookies" in lower or "cookies" in lower or "风控" in msg:
            return "目标平台需要新 cookie，当前下载被限制了"
        if "unable to extract" in lower:
            return "链接识别到了，但目标站点暂时不给直下"
        if "login required" in lower:
            return "这个链接需要登录态 cookie 才能下载"
        if "无法识别抖音视频 id" in msg:
            return msg
        return msg

    async def download_bilibili(self, url: str) -> Path:
        normalized = self.normalize_url(url)
        matched = re.search(r'(BV[0-9A-Za-z]{10})', normalized, flags=re.IGNORECASE)
        if not matched:
            return await self.download_with_ytdlp(url)
        bvid = matched.group(1)
        info = await self.get_bilibili_video_info(bvid)
        if not info:
            return await self.download_with_ytdlp(normalized)
        cid = info.get('cid')
        if not cid:
            return await self.download_with_ytdlp(normalized)
        play_url = await self.get_bilibili_play_url(bvid, cid)
        if not play_url:
            return await self.download_with_ytdlp(normalized)
        target = self.download_dir / f'bilibili_{bvid}.mp4'
        return await self.download_bilibili_mp4(play_url, target)

    async def get_bilibili_video_info(self, bvid: str) -> dict | None:
        url = 'https://api.bilibili.com/x/web-interface/view'
        params = {'bvid': bvid}
        headers = {'User-Agent': self.android_ua, 'Referer': 'https://www.bilibili.com'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url, params=params, headers=headers, ssl=False) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get('code') != 0:
                    return None
                return data.get('data') or None

    async def get_bilibili_play_url(self, bvid: str, cid: int) -> str | None:
        url = 'https://api.bilibili.com/x/player/playurl'
        params = {
            'bvid': bvid,
            'cid': cid,
            'qn': 64,
            'fnval': 1,
            'fourk': 0,
            'platform': 'html5',
        }
        headers = {'User-Agent': self.android_ua, 'Referer': 'https://www.bilibili.com'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url, params=params, headers=headers, ssl=False) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get('code') != 0:
                    return None
                body = data.get('data') or {}
                dash = body.get('dash') or {}
                videos = dash.get('video') or []
                if videos:
                    return videos[0].get('baseUrl') or videos[0].get('base_url')
                durl = body.get('durl') or []
                if durl:
                    return durl[0].get('url')
                return None

    async def download_bilibili_mp4(self, stream_url: str, target: Path) -> Path:
        headers = f"Referer: https://www.bilibili.com\r\nUser-Agent: {self.android_ua}\r\n"
        cmd = ['ffmpeg', '-y', '-headers', headers, '-i', stream_url, '-c', 'copy', str(target)]

        def _run():
            import subprocess
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 or not target.exists() or target.stat().st_size == 0:
                raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'ffmpeg 下载失败')

        await asyncio.to_thread(_run)
        return target

    async def download_with_ytdlp(self, url: str) -> Path:
        outtmpl = str(self.download_dir / '%(extractor)s_%(id)s.%(ext)s')
        opts = {
            'outtmpl': outtmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'format': self.config.get('yt_dlp_format', 'bv*+ba/b[ext=mp4]/b'),
            'http_headers': {
                'User-Agent': self.android_ua,
                'Referer': 'https://www.douyin.com/',
            },
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'cookiefile': self.config.get('cookiefile') or None,
            'extractor_args': {
                'douyin': {
                    'embedder': ['app'],
                }
            },
        }

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                requested = info.get('requested_downloads') or []
                for item in requested:
                    fp = item.get('filepath')
                    if fp and Path(fp).exists():
                        return Path(fp)
                candidate = Path(ydl.prepare_filename(info))
                if candidate.suffix.lower() != '.mp4' and candidate.with_suffix('.mp4').exists():
                    candidate = candidate.with_suffix('.mp4')
                if candidate.exists():
                    return candidate
                stem = candidate.stem
                for maybe in sorted(self.download_dir.glob(f'{stem}*')):
                    if maybe.is_file() and maybe.exists():
                        return maybe
                raise FileNotFoundError(str(candidate))

        path = await asyncio.to_thread(_run)
        if not path.exists():
            raise FileNotFoundError(str(path))
        return path

    async def download_douyin(self, url: str) -> Path:
        redirect_url = await self.fetch_redirect_and_cookie(url)
        logger.info(f"[napcat-media-bridge] douyin redirect: {redirect_url}")
        ty, vid = self.extract_douyin_type_id(redirect_url)
        if not vid:
            raise RuntimeError("无法识别抖音视频 ID")

        try:
            if ty == 'slides':
                media_url = await self.parse_douyin_slides(vid)
                logger.info(f"[napcat-media-bridge] douyin media url: {media_url}")
                return await self.stream_download(media_url, self.download_dir / f"douyin_{vid}.mp4")

            media_url = await self.parse_douyin_video(ty or 'video', vid)
            logger.info(f"[napcat-media-bridge] douyin media url: {media_url}")
            return await self.stream_download(media_url, self.download_dir / f"douyin_{vid}.mp4")
        except Exception as first_error:
            logger.warning(f"[napcat-media-bridge] douyin direct parse failed, fallback to yt-dlp: {first_error}")
            return await self.download_with_ytdlp(url)

    async def fetch_redirect_and_cookie(self, url: str) -> str:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url, headers=self.ios_headers, allow_redirects=False, ssl=False) as resp:
                set_cookie_headers = resp.headers.getall('Set-Cookie', [])
                self._cookie_header = self.merge_set_cookie(set_cookie_headers)
                if self._cookie_header:
                    self.ios_headers['Cookie'] = self._cookie_header
                    self.android_headers['Cookie'] = self._cookie_header
                if resp.status in (301, 302, 303, 307, 308):
                    return resp.headers.get('Location', url)
                return str(resp.url)

    async def parse_douyin_video(self, ty: str, vid: str) -> str:
        urls = [
            f"https://m.douyin.com/share/{ty}/{vid}",
            f"https://www.iesdouyin.com/share/{ty}/{vid}",
        ]
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            for url in urls:
                async with session.get(url, headers=self.ios_headers, allow_redirects=False, ssl=False) as resp:
                    if resp.status != 200:
                        logger.warning(f"[napcat-media-bridge] douyin parse status {resp.status} {url}")
                        continue
                    text = await resp.text()
                    matched = re.search(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", text, flags=re.DOTALL)
                    if not matched or not matched.group(1):
                        logger.warning(f"[napcat-media-bridge] douyin no ROUTER_DATA {url}")
                        continue
                    data = msgspec.json.decode(matched.group(1).strip(), type=RouterData)
                    video_data = data.video_data
                    if video_data.video_url:
                        return video_data.video_url.replace('playwm', 'play')
        raise RuntimeError("分享已删除或资源直链提取失败, 请稍后再试")

    async def parse_douyin_slides(self, vid: str) -> str:
        url = 'https://www.iesdouyin.com/web/api/v2/aweme/slidesinfo/'
        params = {'aweme_ids': f'[{vid}]', 'request_source': '200'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url, params=params, headers=self.android_headers, ssl=False) as resp:
                resp.raise_for_status()
                data = msgspec.json.decode(await resp.read(), type=SlidesInfo)
                first = data.aweme_details[0]
                if first.dynamic_urls:
                    return first.dynamic_urls[0]
        raise RuntimeError('抖音图文没有可下载视频')

    async def stream_download(self, url: str, target: Path) -> Path:
        headers = {'User-Agent': self.ua, 'Referer': 'https://www.douyin.com/'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.get(url, headers=headers, allow_redirects=True, ssl=False) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f'媒体下载失败 HTTP {resp.status}')
                with target.open('wb') as f:
                    async for chunk in resp.content.iter_chunked(1024 * 256):
                        f.write(chunk)
        return target

    def merge_set_cookie(self, headers: list[str]) -> str:
        jar = SimpleCookie()
        for item in headers:
            try:
                jar.load(item)
            except Exception:
                continue
        return '; '.join(f'{k}={m.value}' for k, m in jar.items())

    def extract_douyin_type_id(self, url: str) -> tuple[str | None, str | None]:
        matched = re.search(r'douyin\.com/(?P<ty>video|note)/(?P<vid>\d+)', url)
        if matched:
            return matched.group('ty'), matched.group('vid')
        matched = re.search(r'(?:iesdouyin|m\.douyin)\.com/share/(?P<ty>slides|video|note)/(?P<vid>\d+)', url)
        if matched:
            return matched.group('ty'), matched.group('vid')
        return None, None
