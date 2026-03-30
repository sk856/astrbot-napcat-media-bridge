<div align="center">

# astrbot-napcat-media-bridge

让 AstrBot 自动识别多平台视频链接。
下载后通过 NapCat 原生 `video/file` 消息发送。

</div>

## 是什么

这是一个给 AstrBot 用的媒体桥接插件。

作用只有一件事。
把聊天里的分享链接下载成文件。
再把文件转换成稳定的 HTTP 地址。
最后通过 NapCat 原生消息发出去。

## 解决什么问题

适合下面这些情况。

- AstrBot 能下载文件，但 QQ 发视频不稳定
- 本地绝对路径发不出去
- `file://` 地址经常失败
- 临时文件地址不稳定
- 想把 下载 和 发送 串成自动流程

## 支持平台

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

## 安装

### 1. 放到插件目录

推荐目录名

```text
astrbot_plugin_napcat_media_bridge
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

需要系统已安装 `ffmpeg`。

### 3. 配置插件

参考 `plugin_config.example.json`。

默认配置下，插件启动时会自动

- 创建静态目录
- 写入 Nginx 配置
- 重载 Nginx

### 4. 重载 AstrBot 插件

重载后即可生效。

### 5. 检查状态

给 bot 发送

```text
检查桥接配置
```

如果要重新初始化，发送

```text
初始化静态目录
```

这两个都是插件命令。
通常不需要加 `/`。

### 6. 直接使用

把支持的平台链接发给 bot。
插件会自动处理。

## 配置

### 最常用配置

- `download_dir`
- `static_dir`
- `static_base_url`
- `copy_mode`
- `auto_init_static_dir`
- `auto_init_web_server`
- `auto_reload_nginx`
- `nginx_conf_path`
- `nginx_reload_command`

### 配置说明

#### `download_dir`

下载临时目录。

#### `static_dir`

静态文件目录。

#### `static_base_url`

静态目录对应的访问地址。

示例

```text
http://127.0.0.1:8089/xhs-video
```

如果 NapCat 和 Web 服务不在同一台机器上，不要用 `localhost`。
请改成局域网 IP、容器可达地址或域名。

#### `copy_mode`

发送前文件处理方式。

- `copy` 复制到静态目录后发送
- `reuse` 文件已在静态目录时直接复用

#### `auto_init_static_dir`

启动时自动创建 `static_dir`。

#### `auto_init_web_server`

启动时自动写入 Web 静态映射配置。

#### `auto_reload_nginx`

启动时自动重载 Nginx。

#### `nginx_conf_path`

自动写入的 Nginx 配置路径。

默认值

```text
/www/server/panel/vhost/nginx/openclaw_xhs_static.conf
```

#### `nginx_reload_command`

自动重载 Nginx 使用的命令。

默认值

```bash
nginx -s reload
```

## 默认生成的 Nginx 配置

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

## 命令

### `初始化静态目录`

执行一次完整初始化。

包括

- 创建静态目录
- 写入 Nginx 配置
- 重载 Nginx
- 回显当前配置

### `检查桥接配置`

查看当前桥接状态。

包括

- 静态目录是否存在
- Nginx 配置是否已写入
- 当前访问地址
- 当前重载命令

## 工作流程

1. AstrBot 收到消息
2. 插件提取链接
3. 下载媒体文件
4. 文件进入静态目录
5. 生成 HTTP 地址
6. 通过 NapCat 原生消息发送

## 核心文件

- `plugin_main.py`
- `bridge_sender.py`
- `plugin_config.example.json`
- `references/implementation.md`
- `SKILL.md`

## 排障

优先检查下面几项。

- `static_dir` 是否存在
- `nginx_conf_path` 是否已写入
- Nginx 是否重载成功
- `static_base_url` 是否能访问测试文件
- AstrBot 是否有写权限
- 目标平台是否需要 Cookie
- `yt-dlp` 是否过旧

## 致谢

- `AstrBot` https://github.com/AstrBotDevs/AstrBot
- `NapCatQQ` https://github.com/NapNeko/NapCatQQ
- `yt-dlp` https://github.com/yt-dlp/yt-dlp
- `aiohttp` https://github.com/aio-libs/aiohttp
