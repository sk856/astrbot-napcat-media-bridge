---
name: astrbot-napcat-media-bridge
description: Bridge AstrBot media sending for aiocqhttp/NapCat by converting downloaded local media into stable static HTTP URLs and dispatching native OneBot video/file messages. Use when AstrBot plugins can download media locally but QQ/NapCat fails on direct local paths, file:// URIs, or temporary file-token routes, especially for video sending on qq/aiocqhttp.
---

Expose downloaded media through a stable static HTTP path that NapCat can fetch.

Keep one nginx-served static directory for outgoing media.

Copy freshly-downloaded files into that static directory before sending.

On `aiocqhttp`, bypass generic AstrBot media sending when needed and dispatch native OneBot message dicts with `video` or `file` payloads pointing at the static URL.

Use a fixed URL base such as `http://<host>:8089/xhs-video/<filename>`.

Prefer this flow when QQ/NapCat rejects local file paths, `file://` URIs, or ephemeral tokenized URLs.

For implementation details and file layout, read `references/implementation.md`.
