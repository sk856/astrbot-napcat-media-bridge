from pathlib import Path

from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

STATIC_DIR = Path('/www/wwwroot/openclaw-xhs-video')
STATIC_BASE_URL = 'http://192.168.108.128:8089/xhs-video'


async def send_media_via_napcat(event, local_path: str) -> None:
    """Copy local media to a stable static directory and dispatch a native OneBot media message."""
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(local_path)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    static_path = STATIC_DIR / path.name
    if not static_path.exists() or static_path.stat().st_size != path.stat().st_size:
        static_path.write_bytes(path.read_bytes())

    file_url = f"{STATIC_BASE_URL}/{path.name}"
    msg_type = 'video' if path.suffix.lower() == '.mp4' else 'file'

    bot = getattr(event, 'bot', None)
    raw_event = getattr(event, 'message_obj', None)
    if bot is None:
        raise RuntimeError('aiocqhttp event 缺少 bot 实例')

    is_group = bool(event.get_group_id())
    session_id = event.get_group_id() if is_group else event.get_sender_id()

    logger.info(f'[napcat-media-bridge] dispatch {msg_type}: {file_url}')
    await AiocqhttpMessageEvent._dispatch_send(
        bot=bot,
        event=raw_event,
        is_group=is_group,
        session_id=session_id,
        messages=[{'type': msg_type, 'data': {'file': file_url}}],
    )
