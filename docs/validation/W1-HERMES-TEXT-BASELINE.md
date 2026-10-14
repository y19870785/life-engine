# W1 普通文本体验基线验证

日期：2026-10-14；run ID `w0w1-20261014-01`。范围与固定 Base 见 [W0/W1 基线](../planning/W0-W1-CHARACTER-BASELINE.md)。本文件只记录本批实际取得的结果，不覆盖历史验证原件。

## T0 本地合成

新增三项测试在 `tests/test_character_continuity.py`：独立 CLI 进程重新打开同一 World、重复提交与旧 lease 拒绝；13 轮记录对最近 12 条投影的边界；中文 UTF-8 字节预算下完整原话/剧情的保留。fixture 均为临时目录与原创合成内容，子进程运行本地 CLI，无网络、模型、真实 Host 或外部发送。

既有测试继续覆盖来源分类、开场不重播、不同 World 隔离、取消/截断/压缩拒绝、工具轮拒绝，以及 Memory/Story/journal 部分成功恢复。初次新测试误用 `user_claimed` 字符串，实际合同枚举为 `user_claimed_fact`；已校准测试，未改产品来源语义。

运行结果：Windows Python 3.12，以下两组共 **58 项通过，无跳过**；源码为本分支工作树（本批只改文档与测试，无 Runtime 变更），提交对象由包含本文的 Git 提交确定。

```powershell
py -3.12 -m unittest discover -s tests -p 'test_character*.py' -v
# Ran 27 tests in 25.750s / OK
py -3.12 -X utf8 -m unittest discover -s tests -p 'test_hermes*.py' -v
# Ran 31 tests in 1.411s / OK
```

连续性模块先单独通过 14 项（22.373s），已包含在上述 27 项中，不重复计数。Hermes 分组未加 UTF-8 的初跑有两项既有 `Path.read_text()` 测试受 Windows GBK 默认编码影响；显式 UTF-8 后通过，与仓库 CI 的 `PYTHONUTF8=1` 一致，没有修改测试条件或删除断言。此处不声称整个仓库或远端四矩阵已经通过。

## T1 / T2 与阶段结论

T1 真实调度：NOT_EXECUTED（本仓库记录尚未收到 C 的固定对象证据）。T2 真实 CLI 模型：NOT_EXECUTED。此处不代表 Host 不支持，也不借用先前 PR 的历史观察填充本批结果。

W0 独立审核：PENDING；W1 总体：PENDING。代码未改变现有 12 条/48,000 字节语义；结构化纠正/遗忘、工具轮经历与超窗口检索均 EXPECTED_GAP。provider 请求与退出记录由 C 另行提交，核验后更新本记录。
