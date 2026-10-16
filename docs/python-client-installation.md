# Python client installation / Python 客户端安装

The distribution name is **agent-sandbox-client**; the import is
`agent_sandbox`. The matching in-sandbox runtime distribution is
**agent-sandbox-server**. `pip install agent-sandbox` installs an unrelated
project.

On 2026-10-16 the public PyPI metadata endpoint for `agent-sandbox-client`
returned HTTP 404. Until the packages are published, install both distributions
from the same pinned SDK source commit. Installing only the client would still
require its exact-version server dependency from a package index.

```bash
python3 -m pip install \
  'agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=server-sdk' \
  'agent-sandbox-client @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/35da216a300f1e2e84254a1cf4b4a7ea98681505.tar.gz#subdirectory=client-sdk'
```

For development in sibling checkouts, install the two local distributions
together instead:

```bash
python3 -m pip install -e ../python-sdk/server-sdk -e ../python-sdk/client-sdk
```

Once the matching release exists on your configured index, use
`python3 -m pip install agent-sandbox-client`. The API examples in template
READMEs use the same import with either installation method. Record the SDK
source commit for source installs; version `0.3.0` alone does not identify fixes
made after its version number was set.

客户端发行名是 **agent-sandbox-client**，导入名为 `agent_sandbox`；配套镜像内
运行时发行名是 **agent-sandbox-server**。`pip install agent-sandbox` 是无关项目。

2026-10-16 查询公开 PyPI 客户端元数据返回 HTTP 404。在两个配套包完成发布前，
请使用上面的固定提交同时安装两个发行包；仅从源码安装客户端，仍会尝试从索引
获取其精确版本的服务端依赖。本地并列仓库开发可以同时 editable 安装。

配置的包索引具备配套版本后，再使用 `python3 -m pip install agent-sandbox-client`。
README 中的 SDK 示例适用于这两种安装方式。源码验收请同时记录 SDK 提交，
不要仅凭 `0.3.0` 版本号判断是否包含后续修复。
