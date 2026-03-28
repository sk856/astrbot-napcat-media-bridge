# astrbot-napcat-media-bridge

把 AstrBot 本地下载好的媒体文件转换成 NapCat 更稳定可发送的 HTTP 静态地址，再走原生 OneBot `video/file` 消息发出去。

## 现状

这个仓库先整理出本次实测打通的核心发送逻辑。

- 小红书视频发送已验证可用
- B站视频发送链路已打通到自动下载 + 直接发视频
- 关键思路不是直接给 NapCat 本地路径
- 而是先映射到稳定静态 URL，再发原生 `video` 消息

## 核心文件

- `bridge_sender.py`
- `SKILL.md`
- `references/implementation.md`

## 核心流程

1. 插件把视频下载到本地
2. 拷贝到 nginx 可读目录
3. 生成稳定 URL
4. 通过 `AiocqhttpMessageEvent._dispatch_send` 发原生消息

## 为什么需要这个桥接

NapCat/QQ 在很多情况下对这些输入不稳定

- 本地绝对路径
- `file://` URI
- 临时 token 文件路由

而稳定的静态 HTTP 文件 URL 更容易成功。
