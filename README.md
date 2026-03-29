<div align="center">

# astrbot-napcat-media-bridge

让 AstrBot 自动识别多平台视频链接
下载后走 NapCat 原生消息稳定发出

支持 抖音 小红书 B站 微博 快手 西瓜 YouTube TikTok X 等常见链接

[快速开始](#快速开始) / [配置说明](#配置说明) / [支持平台](#支持平台) / [工作原理](#工作原理) / [注意事项](#注意事项)

</div>

## 项目简介

这个插件的目标很直接。

就是把 AstrBot 收到的分享链接自动识别出来，下载媒体文件，再通过 NapCat 原生 `video/file` 消息发出去，尽量避开 QQ 对本地路径、临时文件和不稳定文件 URI 的各种抽风。

它不是简单转发文本。
它会真的去下载，然后把文件桥接成稳定静态地址，再发原生媒体消息。

## 功能特点

- 自动识别聊天里的视频链接
- 自动下载媒体文件并回传
- 优先兼容 NapCat 原生 `video/file` 发送
- 支持把本地文件复制到静态目录后再发送
- 支持直接复用已有静态目录文件
- 对 B 站短链和 `BV` 链接做了单独处理
- 对常见下载失败场景提供更可读的报错

## 当前状态

目前已经完成一版可用链路。

- 小红书视频发送已验证
- B 站分享链接已补齐自动下载与发送流程
- NapCat 静态 URL 桥接发送已经跑通
- 插件默认支持自动监听消息，无需单独命令触发

## 快速开始

### 1. 放置插件

把仓库内容放到 AstrBot 插件目录中。

推荐目录名

```text
astrbot_plugin_napcat_media_bridge
```

### 2. 安装依赖

按 AstrBot 插件加载方式安装 `requirements.txt` 里的依赖。

### 3. 准备静态文件目录

需要准备一个能被 QQ 访问到的静态目录和对应 URL。

常见做法是

- Nginx 暴露一个目录
- 插件把下载好的文件复制进去
- NapCat 发送这个文件对应的 HTTP 地址

### 4. 配置插件

可参考 `plugin_config.example.json`。

最关键的是这几个值

- `static_dir`
- `static_base_url`
- `copy_mode`
- `download_dir`

### 5. 重载插件

重载 AstrBot 插件后，往聊天里直接发链接就行。

插件识别到支持的平台链接后，会自动下载并发送。

## 配置说明

### `download_dir`

下载文件的临时目录。

### `static_dir`

静态文件落盘目录。

这个目录需要能被 Web 服务读取。

### `static_base_url`

静态目录对应的外部访问地址。

例如

```text
http://127.0.0.1:8089/xhs-video
```

如果发往 QQ 的客户端设备不在本机，通常要改成局域网可访问或公网可访问地址。

### `copy_mode`

控制发送前怎么处理文件。

可用思路

- `copy` 先复制再发送
- `reuse` 如果文件已经在静态目录里就直接复用

### `enable_auto_detect`

是否开启自动识别消息里的链接。

默认开启。

## 支持平台

当前代码里已经覆盖这些常见链接来源。

- 抖音
- 小红书
- Bilibili
- 微博
- 快手
- 西瓜视频
- YouTube
- Instagram
- TikTok
- X / Twitter

其中不同平台的稳定性会受目标站点风控、Cookie、地区限制和下载器支持情况影响。

## 工作原理

整体流程很简单。

1. AstrBot 收到聊天消息
2. 插件从消息文本和组件里提取链接
3. 按平台规则整理链接
4. 下载媒体文件
5. 将文件放进静态目录或复用已有文件
6. 生成稳定 HTTP 地址
7. 通过 NapCat 原生 `video/file` 消息发出

B 站这块额外做了几件事。

- 自动展开 `b23.tv` 这类短链
- 自动提取 `BV` 号并归一化链接
- 优先走 B 站视频信息和播放地址逻辑
- 不行时再回退到 `yt-dlp`

## 核心文件

- `plugin_main.py` 插件主逻辑
- `bridge_sender.py` NapCat 原生消息桥接发送
- `plugin_config.example.json` 示例配置
- `references/implementation.md` 实现笔记
- `SKILL.md` 项目说明与上下文

## 适合什么场景

如果你已经遇到这些问题，这个插件就很适合。

- AstrBot 能下载，但 NapCat 发视频不稳定
- 本地绝对路径发不出去
- `file://` 地址经常失败
- 机器人收到分享链接后想自动回传视频
- 想把下载和发送串成一个自动流程

## 注意事项

- `static_base_url` 必须真的可访问，不然 NapCat 发出去也没法拉取文件
- 某些平台会因为风控、Cookie 过期或登录限制导致下载失败
- B 站、抖音这类站点策略变化快，后面可能还需要继续跟进
- 如果文件很大，发送成功率也会受 QQ 侧限制影响

## 排障建议

如果链接识别到了但还是失败，优先看这几类问题。

- 静态目录是否能正常对外访问
- Web 服务是否真的能访问到文件
- AstrBot 运行用户是否有写入权限
- NapCat 当前是否健康
- 目标平台是否需要新 Cookie
- `yt-dlp` 或相关依赖是否过旧

## 后续计划

这版先把自动识别、下载和稳定发送链路打通。

后面可以继续补的方向包括

- 更完整的配置文档
- 更细的平台级错误提示
- 命令式手动触发入口
- 更多平台的专门下载逻辑
- 更完整的安装示例

## 致谢

这个仓库是在一堆现成项目和实际环境上边修边打磨出来的。

特别感谢这些项目和参考来源。

- `AstrBot` https://github.com/AstrBotDevs/AstrBot
- `NapCatQQ` https://github.com/NapNeko/NapCatQQ
- `yt-dlp` https://github.com/yt-dlp/yt-dlp
- `aiohttp` https://github.com/aio-libs/aiohttp
- `chatanywhere/GPT_API_free` https://github.com/chatanywhere/GPT_API_free

如果它正好也帮你省掉了一堆折腾，那就值了。