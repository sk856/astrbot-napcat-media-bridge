from pathlib import Path
import shutil

from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent


async def send_media_via_napcat(
    event,
    local_path: str,
    static_dir: str = "/www/wwwroot/openclaw-xhs-video",
    static_base_url: str = "http://127.0.0.1:8089/xhs-video",
    copy_mode: str = "copy",
) -> None:
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(local_path)

    target_dir = Path(static_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if copy_mode == "reuse" and path.parent.resolve() == target_dir.resolve():
        static_path = path
    else:
        static_path = target_dir / path.name
        if not static_path.exists() or static_path.stat().st_size != path.stat().st_size:
            shutil.copy2(path, static_path)

    file_url = f"{static_base_url.rstrip('/')}/{static_path.name}"
    suffix = static_path.suffix.lower()
    msg_type = "video" if suffix in {".mp4", ".mov", ".m4v", ".webm"} else "file"

    bot = getattr(event, "bot", None)
    raw_event = getattr(event, "message_obj", None)
    if bot is None:
        raise RuntimeError("aiocqhttp event 缺少 bot 实例")

    is_group = bool(event.get_group_id())
    session_id = event.get_group_id() if is_group else event.get_sender_id()

    logger.info(f"[napcat-media-bridge] dispatch {msg_type}: {file_url}")
    await AiocqhttpMessageEvent._dispatch_send(
        bot=bot,
        event=raw_event,
        is_group=is_group,
        session_id=session_id,
        messages=[{"type": msg_type, "data": {"file": file_url}}],
    )
