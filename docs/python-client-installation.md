# Python client installation / Python 客户端安装

Install the published preview client and its matching server dependency:

```bash
python3 -m pip install 'agent-sandbox-client==0.3.1a2'
```

The import is `agent_sandbox`. `agent-sandbox-server` is the in-sandbox service;
`pip install agent-sandbox` installs an unrelated project. The client dependency
installs the matching server distribution automatically. Preview versions are
explicit here because pip does not select them by default.

For local SDK development, install both distributions from the same checkout:

```bash
python3 -m pip install -e /path/to/python-sdk/server-sdk -e /path/to/python-sdk/client-sdk
```

安装已发布的预览客户端，配套服务端依赖会自动安装。导入名是 `agent_sandbox`；
镜像内服务包是 `agent-sandbox-server`。`pip install agent-sandbox` 是无关项目。
pip 默认不选择预览版，因此上面的命令明确指定版本。开发 SDK 时，从同一个源码目录
同时安装两个发行包，并将示例中的路径替换为实际目录。
