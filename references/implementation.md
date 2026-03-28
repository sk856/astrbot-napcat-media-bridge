# Implementation

## Goal

Turn locally downloaded media into a QQ-sendable video or file by:

1. Downloading media to local disk
2. Copying it into an nginx-readable static directory
3. Sending a native OneBot `video` or `file` message that points to the static HTTP URL

## Proven layout

- Static directory: `/www/wwwroot/openclaw-xhs-video`
- Static base URL: `http://192.168.108.128:8089/xhs-video`
- Nginx vhost: `/www/server/panel/vhost/nginx/openclaw_xhs_static.conf`

## Nginx example

Use a dedicated server block:

```nginx
server {
    listen 8089;
    server_name _;
    autoindex off;

    location /xhs-video/ {
        alias /www/wwwroot/openclaw-xhs-video/;
        add_header Cache-Control no-store;
        types { video/mp4 mp4; application/octet-stream bin; }
        default_type application/octet-stream;
    }
}
```

Reload nginx after changes.

## AstrBot sender pattern

In the sending layer:

- Detect aiocqhttp platform
- Detect any outgoing segment carrying a local file path
- Copy the file into `/www/wwwroot/openclaw-xhs-video/<filename>`
- Build URL `http://192.168.108.128:8089/xhs-video/<filename>`
- Dispatch native OneBot messages through `AiocqhttpMessageEvent._dispatch_send`

Pattern:

```python
from pathlib import Path
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

static_dir = Path('/www/wwwroot/openclaw-xhs-video')
static_dir.mkdir(parents=True, exist_ok=True)

file_name = Path(local_path).name
static_path = static_dir / file_name
static_path.write_bytes(Path(local_path).read_bytes())
file_url = f'http://192.168.108.128:8089/xhs-video/{file_name}'

await AiocqhttpMessageEvent._dispatch_send(
    bot=bot,
    event=raw_event,
    is_group=is_group,
    session_id=session_id,
    messages=[{"type": "video", "data": {"file": file_url}}],
)
```

Use `type=file` for non-video payloads.

## Why this works

NapCat often fails on:

- direct local absolute paths
- `file://` URIs
- temporary token routes that return tiny HTML error pages instead of media bytes

NapCat accepts a stable HTTP URL much more reliably.

## Bilibili note

Bilibili downloading may need a separate fetch step. The send side should still reuse this same static-URL + native-video dispatch pattern.

## Files touched in the working setup

- `astrbot-data/data/plugins/astrbot_plugin_parser/core/sender.py`
- `astrbot-data/data/plugins/astrbot_plugin_parser/core/parsers/xhs.py`
- `astrbot-data/data/plugins/astrbot_plugin_biliVideo/main.py`
- `astrbot-data/data/plugins/astrbot_plugin_biliVideo/services/bilibili_api.py`
- `astrbot-data/data/plugins/astrbot_plugin_biliVideo/services/video_dl.py`
