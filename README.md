<div align="center">

# astrbot-napcat-media-bridge

让 AstrBot 自动识别多平台视频链接。
下载后通过 NapCat 原生 `video/file` 消息发送。

</div>

## 用途

把聊天里的分享链接识别出来。
下载媒体文件。
把文件放到静态目录。
通过 HTTP 地址发给 NapCat。

## 功能

- 自动识别常见视频链接
- 自动下载媒体文件
- 通过 NapCat 原生 `video/file` 发送
- 支持静态目录复制和复用
- 支持 B 站短链和 `BV` 链接处理
- 对常见失败场景返回可读错误

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

### 1. 放置插件

把仓库放到 AstrBot 插件目录。

推荐目录名

```text
astrbot_plugin_napcat_media_bridge
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

还需要系统已安装 `ffmpeg`。

### 3. 配置插件

参考 `plugin_config.example.json`。

常用配置项

- `download_dir`
- `static_dir`
- `static_base_url`
- `copy_mode`
- `auto_init_static_dir`
- `auto_init_web_server`
- `auto_reload_nginx`
- `nginx_conf_path`
- `nginx_reload_command`

默认情况下，插件启动时会自动

- 创建 `static_dir`
- 写入 `nginx_conf_path`
- 执行 `nginx_reload_command`

### 4. 重载插件

重载 AstrBot 插件。

### 5. 检查结果

给 bot 发送

```text
检查桥接配置
```

如果需要手动重跑初始化，发送

```text
初始化静态目录
```

这两个都是发给 bot 的插件命令。
通常不需要加 `/`。

### 6. 开始使用

把支持的平台链接直接发给 bot。
插件会自动下载并发送。

## 配置说明

### `download_dir`

下载文件的临时目录。

### `static_dir`

静态文件目录。

### `static_base_url`

静态目录对应的访问地址。

示例

```text
http://127.0.0.1:8089/xhs-video
```

如果 NapCat 和 Web 服务不在同一台机器上，不要用 `localhost`。
改成局域网 IP、容器可达地址或域名。

### `copy_mode`

发送前的文件处理方式。

- `copy` 复制到静态目录后发送
- `reuse` 文件已在静态目录时直接复用

### `auto_init_static_dir`

启动时自动创建 `static_dir`。

### `auto_init_web_server`

启动时自动写入 Web 静态映射配置。

### `auto_reload_nginx`

启动时自动执行 Nginx 重载。

### `nginx_conf_path`

自动写入的 Nginx 配置路径。

默认值

```text
/www/server/panel/vhost/nginx/openclaw_xhs_static.conf
```

### `nginx_reload_command`

自动重载 Nginx 使用的命令。

默认值

```bash
nginx -s reload
```

## 默认生成的 Nginx 配置

插件会按配置生成静态映射。
默认效果如下

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

## 管理命令

- `初始化静态目录`
- `检查桥接配置`

## 工作原理

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

## 注意事项

- `static_base_url` 必须能实际访问
- 某些平台可能需要有效 Cookie
- `yt-dlp` 和平台策略变化会影响下载成功率
- 大文件发送会受 QQ 侧限制影响

## 排障

优先检查

- `static_dir` 是否存在
- `nginx_conf_path` 是否已写入
- Nginx 是否重载成功
- `static_base_url` 是否能访问到测试文件
- AstrBot 是否有写权限
- 目标平台是否需要 Cookie

## 致谢

- `AstrBot` https://github.com/AstrBotDevs/AstrBot
- `NapCatQQ` https://github.com/NapNeko/NapCatQQ
- `yt-dlp` https://github.com/yt-dlp/yt-dlp
- `aiohttp` https://github.com/aio-libs/aiohttp
