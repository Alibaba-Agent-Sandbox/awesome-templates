# 在本机预览自有沙箱中的 Web 应用

[English](preview-proxy.md)。此工具运行在与浏览器同一台电脑上的配套原生 Python
SDK 环境中。阿里云默认 FC 域名可能把 HTML 标为附件，见[官方说明](https://www.alibabacloud.com/help/en/functioncompute/web-functions)。
已有自定义预览域名仍可使用直接模式。本地方式访问真实远端应用，保留上游 HTTPS
证书验证，并通过只监听回环地址的客户端转发 HTTP/WebSocket。

## 安装与打开

已测试的操作端环境是 Linux amd64、CPython3.13，先安装[配套原生客户端](python-client-installation.md)。在本仓库执行：

```bash
python -m pip install --require-hashes -r scripts/requirements-preview.txt
python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 8443
```

将 ID 替换为调用者独占且已启动密码认证 code-server 的沙箱。远端端口默认8443，
其他自有应用可选择1–65535的整数端口。在运行代理的同一台电脑上打开输出的私有
本地 URL，完成真实应用登录。Ctrl+C 关闭代理。应用停止和沙箱销毁由调用者负责；
代理只关闭本地监听、HTTP/WS 客户端和内存 cookie jar，不创建或销毁借用的沙箱。

初始 URL 含随机本地访问能力，后续请求需 HttpOnly、SameSite=Strict 的本地 cookie。
Host、Origin 仅接受当前回环来源。应用 cookie 单独保存在本次代理的内存中，不向
上游发送浏览器或其他本地端口的 cookie。目标始终为 SDK 返回的固定端点；浏览器
query 不能覆盖 SDK 的认证 query。保留操作端代理设置，不自动加载 netrc 凭据。
请保持输出的本地 URL 私有。

## HTTP、WebSocket 与限制

仅对 text/html 去除 attachment Content-Disposition，保留其他下载、压缩响应字节、
应用内容和状态码。HTTP 响应带背压流式转发；请求体上限16MiB，单个 WebSocket
消息上限8MiB，HTTP 请求预算300秒。转发文本/二进制帧和协商的子协议；拒绝跳转
到固定自有端点以外。这是本机预览操作，不是公共托管服务，也不证明默认 FC 域名
能直接渲染 HTML。

上游始终验证 HTTPS 证书和主机名。本机浏览器通过127.0.0.1上的 HTTP 访问，不做
浏览器响应拦截或页面替换。工具和依赖只在操作端使用，不修改模板镜像/运行时，
也不移除应用认证。

## 验证 code-server

现有独立浏览器控制器需要 Playwright1.58.0、其 Chromium revision1208，以及
certutil（Debian 包 libnss3-tools）。在调用者独占、尚未启动 IDE 的沙箱执行：

```bash
python code-server/browser_e2e_test.py --sandbox-id <owned-sandbox-id> --preview-mode sdk-local
```

控制器启动真实密码认证 IDE，在 Chromium 加载 JavaScript workbench，通过真实
终端 WebSocket 写入随机文件，再用 Monaco 编辑/保存，并通过文件 SDK 独立读回。
最后停止本次 IDE、删除本次文件、关闭本地代理，沙箱销毁仍由调用者负责。
默认 --preview-mode direct 保留直接域名检查，该模式下 HTML 被强制下载仍失败。
结果明确记录预览模式、上游 TLS 和清理。当前云端结果见模板[已验证部分](../code-server/README.zh-CN.md#已验证)。
