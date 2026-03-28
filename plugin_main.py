from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent


class NapCatMediaBridgePlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config or {}
        self.static_dir = Path(self.config.get('static_dir', '/www/wwwroot/openclaw-xhs-video'))
        self.static_base_url = self.config.get('static_base_url', 'http://192.168.108.128:8089/xhs-video')

    async def send_local_media(self, event: AstrMessageEvent, local_path: str):
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(local_path)

        self.static_dir.mkdir(parents=True, exist_ok=True)
        static_path = self.static_dir / path.name
        if not static_path.exists() or static_path.stat().st_size != path.stat().st_size:
            static_path.write_bytes(path.read_bytes())

        file_url = f"{self.static_base_url}/{path.name}"
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

    @filter.command('桥接发送', alias={'bridge_send'})
    async def bridge_send_cmd(self, event: AstrMessageEvent):
        text = (event.message_str or '').strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result('❌ 请提供本地文件路径')
            return
        local_path = parts[1].strip()
        try:
            await self.send_local_media(event, local_path)
            yield event.plain_result('✅ 已尝试桥接发送')
        except Exception as e:
            logger.error(f'桥接发送失败: {e}', exc_info=True)
            yield event.plain_result(f'❌ 桥接发送失败: {e}')
