# 用原生平台步骤构建并测试模板

[English](platform-steps.md)。该维护入口在阿里云极速版准备模板，不需要本地 Docker。
常规公开启动见[模板使用指南](using-templates.zh-CN.md)。步骤构建与 Docker 镜像
构建是不同的验证范围。

按[安装指南](using-templates.zh-CN.md)安装当前已发布 CLI 和 Python client/server，
再安装本仓库检查器及对应控制器依赖。通过进程环境提供已有极速版账号；这些命令
不会把凭据上传到 Actions。

```bash
python -m pip install -r scripts/requirements-spec.txt
python scripts/run_steps_e2e.py python-hello --timeout 900
```

该命令始终运行完整应用控制器：从选定 Dockerfile 生成原生步骤，调用 provider 原生
准备接口，等待本次模板 READY，然后将准备好的 ID 和原清单的启动、就绪、服务及环境
声明写入临时托管清单，调用当前 `abx template launch`。随后通过 CLI、Python 应用
客户端及 HTTP 调用命名命令，检查实际源码、文件和进程操作，最后独立销毁并核对
沙箱及准备模板不存在。只有一条启动路径，没有 CLI／SDK 两种创建选项。

内部 `template deploy --build steps` 只负责准备，不预先启动另一套应用，也不替代
公开启动。原生状态必须是实际 JSON 字符串或对象，不接受 Python repr 字符串。
公开 `template launch` 不增加 `--build steps` 参数。

## 不创建云资源，只检查准备结果

```bash
python scripts/prepare_steps.py python-hello --output /tmp/python-hello-steps
```

输出目录必须是新目录。转换保留 RUN、ENV、WORKDIR、USER 的顺序及 heredoc／续行；
仅传输明确的公开 COPY 输入，并核对哈希和文件模式。缺失、私有或越界输入在云端
提交前失败。较大配方从不可变公开提交获取源码归档并核对全部字节；先公开准确提交，
再执行云端构建。原 Dockerfile 直接从官方 PyPI 安装已发布 server 0.4.0a2，没有
注入 wheel、Git 服务端回退或服务端源码选择器。

默认基础镜像解析为 `cn-hangzhou`、`v0.0.49`。只有主动选择其他基础镜像时才设置
`--region`／`--base-tag`；基础 PATH 变化必须通过已验证的 `--base-path` 明确提供。
运行身份保留非 root `user`，仅原安装步骤需要时在准备中使用 root。

## 较大公开资产

`--asset-transport parallel` 对已审查上游归档进行有界并行请求；`--asset-transport oss`
使用临时私有同账号缓存，需要可选本地 SDK。两者核对声明的大小和哈希，保留原有
15,000 字节 provider 传输限制，不放宽归档大小、原厂软件或凭据边界。仅已审查的
Muse 资产保留其准确大小例外。OSS 缓存也必须独立核对不存在才能 PASS。
`ABX_STEP_LOCAL_ARCHIVE_DIR` 的本地复用仍须通过全部原始大小／哈希检查。

## 证据与失败

每次尝试写入不同的 `evidence/verification-steps-<timestamp>.json`。通过必须同时满足
应用控制器、沙箱清理、准备模板清理及可选资产缓存清理。失败在 checkout 外保留
私有 staging／journal 供恢复本次资源；公开回执只含受控失败类别，不含私有 URL、ID
或凭据。真实模型／原厂账号跳过仍表示未验证，不能继承冒烟结果。
矩阵发现本次资源清理不明时，在创建下一个模板前停止；只恢复准确记录的本次资源，
然后显式选择其余模板继续。

历史[44 模板原生检查点](../.agents/evidence/verify/2026-10-21-current-native-http44.json)
及其他日期回执保留其准确版本和调用入口，不认证当前服务包固定版本或迁移后的启动
消费者；新云端及镜像结果分别记录。
