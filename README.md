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

现在默认就是保守模式的一键初始化。

重载插件后，插件会自动尝试做两件事

- 创建 `static_dir`
- 把 Nginx 静态映射配置写到 `nginx_conf_path`

也就是说，大多数情况下你装完插件后，Web 端配置已经被插件提前写好了。

如果你想手动再执行一次，也可以直接给 bot 发送

```text
初始化静态目录
```

如果只想看当前状态，就发送

```text
检查桥接配置
```

这两个都是发给 bot 的插件命令。
不是终端命令。
通常也不需要加 `/`。

#### 默认自动做了什么

插件会尝试保证下面几项就绪

- `static_dir` 已创建
- `nginx_conf_path` 已写入 Nginx 配置文件
- `static_base_url` 和静态映射路径保持一致

默认示例是

- `static_dir` 为 `/www/wwwroot/openclaw-xhs-video`
- `static_base_url` 为 `http://127.0.0.1:8089/xhs-video`
- `nginx_conf_path` 为 `/www/server/panel/vhost/nginx/openclaw_xhs_static.conf`

如果 NapCat 和这个 Web 服务就在同一台机器上，可以直接用 `127.0.0.1`。
如果不是同机访问，就把 `static_base_url` 改成局域网 IP、容器可达地址或域名，不要写 `localhost`。

#### 插件自动写入的 Nginx 配置长什么样

插件会按你的配置自动生成一份静态映射。
效果等价于下面这份

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

如果你改了 `static_dir`、`static_base_url` 或 `nginx_conf_path`，插件写出的内容也会跟着变。

#### 现在还需要你手动做什么

保守模式下，插件不会替你自动重载 Nginx。
所以通常还差最后一步

```bash
nginx -s reload
```

或者用你当前面板自己的重载方式。

这一步做完，静态映射通常就生效了。

#### 怎么验证已经接近即装即用

最稳的方式是

1. 安装插件并重载
2. 给 bot 发 `检查桥接配置`
3. 确认 `static_dir_exists` 和 `nginx_conf_exists` 都是正常的
4. 在宿主机重载一次 Nginx
5. 丢一个测试文件到 `static_dir`
6. 用浏览器访问 `static_base_url/文件名`

比如

- 文件路径是 `/www/wwwroot/openclaw-xhs-video/test.mp4`
- 对应访问地址就是 `http://127.0.0.1:8089/xhs-video/test.mp4`

如果浏览器能打开或开始下载，后面把真实视频链接发给 bot 就可以直接走通。

#### 什么时候会失败

最常见就两种情况

- 插件进程对 `nginx_conf_path` 没有写权限
- 宿主机没有按预期加载这个 Nginx 配置目录

如果碰到这种情况，插件至少还是会把目录和配置内容准备好。
你只需要补宿主机那一步，不用再手抄配置。

### 4. 配置插件

可参考 `plugin_config.example.json`。

最关键的是这几个值

- `static_dir`
- `static_base_url`
- `copy_mode`
- `download_dir`
- `auto_init_static_dir`
- `auto_init_web_server`
- `nginx_conf_path`

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

### `auto_init_web_server`

插件启动时是否自动尝试写入 Web 静态映射配置。

默认开启。

保守模式下，它会把 Nginx 配置写到 `nginx_conf_path`。
但不会自动替你重载 Nginx。

### `nginx_conf_path`

插件自动写入 Nginx 静态映射配置的目标路径。

默认值是

```text
/www/server/panel/vhost/nginx/openclaw_xhs_static.conf
```

如果你的宿主机 Nginx 配置目录不同，这里也要一起改。

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