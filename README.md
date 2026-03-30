<div align="center">

# astrbot-napcat-media-bridge

让 AstrBot 自动识别多平台视频链接
下载后走 NapCat 原生消息稳定发出

支持 抖音 小红书 B站 微博 快手 西瓜 YouTube TikTok X 等常见链接

[快速开始](#快速开始) / [配置说明](#配置说明) / [支持平台](#支持平台) / [工作原理](#工作原理) / [注意事项](#注意事项)

</div>

## 项目简介

这个插件用来处理一件事。

把 AstrBot 收到的分享链接自动识别出来，下载媒体文件，再通过 NapCat 原生 `video/file` 消息发出去。

核心思路不是直接把本地路径丢给 QQ。
而是先把文件桥接成稳定的 HTTP 静态地址，再发原生媒体消息。

## 功能特点

- 自动识别聊天里的视频链接
- 自动下载媒体文件并回传
- 优先兼容 NapCat 原生 `video/file` 发送
- 支持把本地文件复制到静态目录后再发送
- 支持直接复用已有静态目录文件
- 对 B 站短链和 `BV` 链接做了单独处理
- 对常见下载失败场景提供更可读的报错

## 当前状态

目前已经有一版可直接使用的链路。

- 小红书视频发送已验证
- B 站分享链接已补齐自动下载与发送流程
- NapCat 静态 URL 桥接发送已经跑通
- 插件默认支持自动监听消息，不需要手动命令触发下载

## 快速开始

### 1. 放置插件

把仓库内容放到 AstrBot 插件目录中。

推荐目录名

```text
astrbot_plugin_napcat_media_bridge
```

### 2. 安装依赖

先安装插件依赖。

```bash
pip install -r requirements.txt
```

当前依赖包括

- `aiohttp`
- `msgspec`
- `yt-dlp`

如果你的环境里没有 `ffmpeg`，也要另外装好。

### 3. 准备静态文件目录和 Web 服务映射

这一步的目标很简单。

就是让插件写入的 `static_dir`，能被 Web 服务映射成一个稳定的 HTTP 地址。
这样 NapCat 才能从这个地址拉到视频文件。

整个流程可以按下面做。

#### 第一步 让插件先把目录准备出来

重载插件后，直接给 bot 发送一条消息

```text
初始化静态目录
```

不需要去服务器终端执行。
这是一条发给 bot 的插件命令消息。
通常也不需要加 `/`。

它会做这些事

- 自动创建 `static_dir`
- 回显当前桥接配置
- 输出一段可直接参考的 Nginx 配置

如果你想先检查当前配置，也可以直接给 bot 发送

```text
检查桥接配置
```

这同样是插件命令消息。

#### 第二步 确认插件配置里的两个关键值

最少要确认这两个值是对应的

- `static_dir` 例如 `/www/wwwroot/openclaw-xhs-video`
- `static_base_url` 例如 `http://192.168.108.128:8089/xhs-video`

如果 NapCat 和这个 Web 服务就在同一台机器上，`static_base_url` 也可以写成 `http://127.0.0.1:8089/xhs-video`。
如果不是同机访问，就不要写 `localhost`。

它们的关系要一一对应。

比如说

- 插件把文件写到 `/www/wwwroot/openclaw-xhs-video/test.mp4`
- Web 服务就要能通过 `http://192.168.108.128:8089/xhs-video/test.mp4` 访问到它

#### 第三步 在宿主机上配置 Nginx 映射

这一段不是发给 bot 的。
这一步要在服务器上操作。

可以新建一个 Nginx 配置文件。
例如

```text
/www/server/panel/vhost/nginx/openclaw_xhs_static.conf
```

内容可以用下面这份

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

如果你配置里的 `static_dir` 不是 `/www/wwwroot/openclaw-xhs-video`，这里的 `alias` 也要一起改。

如果你配置里的 `static_base_url` 路径不是 `/xhs-video`，这里的 `location` 也要一起改。

#### 第四步 重载 Nginx

保存配置后，重载 Nginx 让映射生效。

常见做法是

```bash
nginx -s reload
```

或者用你当前面板自己的重载方式。

#### 第五步 手动访问一个测试文件

最稳的验证方式是，先往 `static_dir` 里放一个测试文件，然后直接在浏览器里访问它。

比如

```text
/www/wwwroot/openclaw-xhs-video/test.mp4
```

然后访问

```text
http://192.168.108.128:8089/xhs-video/test.mp4
```

如果浏览器能打开或开始下载，说明映射通了。

#### 第六步 再让 bot 处理真实链接

等 Web 映射确认没问题后，再把视频链接发给 bot。

这时候完整链路才是通的

- 插件下载文件
- 插件把文件复制到 `static_dir`
- NapCat 通过 `static_base_url` 对应的 HTTP 地址发视频

如果这里没配通，就会出现文件明明下载了，但 QQ 侧还是发不出去的情况。

### 4. 配置插件

可参考 `plugin_config.example.json`。

最关键的是这几个值

- `static_dir`
- `static_base_url`
- `copy_mode`
- `download_dir`
- `auto_init_static_dir`

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

静态目录对应的可访问 HTTP 地址。

例如

```text
http://127.0.0.1:8089/xhs-video
```

这一项不要只看自己浏览器能不能打开。
要看真正拉取文件的那一端能不能访问到。

可以这样判断

- 如果 NapCat 和 Web 服务在同一台机器上，通常可以用 `127.0.0.1`
- 如果 NapCat 在 Docker 里，`127.0.0.1` 往往会指向容器自己，这时通常不能直接用
- 如果拉取方不在这台宿主机上，就要改成局域网 IP、容器可达地址，或者公网域名

所以 `localhost` 或 `127.0.0.1` 不是一定不能用。
但只有在拉取方和 Web 服务确实是同机可达时才适合。

### `copy_mode`

控制发送前怎么处理文件。

可用思路

- `copy` 先复制再发送
- `reuse` 如果文件已经在静态目录里就直接复用

### `enable_auto_detect`

是否开启自动识别消息里的链接。

默认开启。

### `auto_init_static_dir`

插件启动时是否自动尝试创建 `static_dir`。

默认开启。

这能解决目录不存在的问题。
但 Web 服务映射本身还是需要宿主机完成。

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

## 管理命令

插件现在额外提供两个管理命令。

- `初始化静态目录` 创建静态目录并输出建议的 Nginx 配置
- `检查桥接配置` 查看当前桥接相关配置是否完整

## 后续计划

后面可以继续补的方向包括

- 更完整的配置文档
- 更细的平台级错误提示
- 一键生成宿主机静态配置模板
- 更多平台的专门下载逻辑
- 更完整的安装示例

## 致谢

特别感谢这些项目和参考来源。

- `AstrBot` https://github.com/AstrBotDevs/AstrBot
- `NapCatQQ` https://github.com/NapNeko/NapCatQQ
- `yt-dlp` https://github.com/yt-dlp/yt-dlp
- `aiohttp` https://github.com/aio-libs/aiohttp

如果它正好也帮你省掉了一堆折腾，那就值了。