# X1 本地试用：跨会话记忆与虚拟日常

这是一份**合成数据样机**，只验证 C01/C04 的 Core 状态和供模型使用的事实包。它不连接模型、真实 Host 或网络，输出固定标记 `MODEL_NOT_CONNECTED`；当前不能据此判定「活人感」通过。建议在 Windows PowerShell 中从仓库根目录运行，使用 Python 3.12。所有安装状态都建在系统临时目录下的新实例，不读取现有聊天或角色卡。

```powershell
py -3.12 -X utf8 examples/experience_x1.py init
```

记下输出中的 `sandbox` 路径。下面把它设为 `$x1`，只替换引号内的路径：

```powershell
$x1 = '把 init 输出的 sandbox 路径粘贴到这里'
py -3.12 -X utf8 examples/experience_x1.py day0 --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py day0 --accept --sandbox $x1
```

第一条 `day0` 只预览「明天下午有个面试，我有点紧张」，不会保存。`--accept` 明确接受这条合成原话为 Soul World 记忆。若要用 Hermes 评价**措辞与世界感**，现在先导出 Day 0 提示，复制到独立测试 Profile 的一个全新会话：

```powershell
py -3.12 -X utf8 examples/experience_x1.py hermes-prompt --day 0 --sandbox $x1
```

此时 Core 中读书为 `ACTIVE`、散步为 `PLANNED`，提示直接读取这些状态。必须先导出 Day 0，再推进 Day 1；推进后反向导出会返回 `CLOCK_REGRESSION`。更新样机后请用 `init` 创建新实例进行完整试用。

现在关闭 PowerShell，重新打开一个窗口，仍在仓库根目录运行：

```powershell
$x1 = '同一个 sandbox 路径'
py -3.12 -X utf8 examples/experience_x1.py day1 --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py day1 --sandbox $x1 --message '你怎么知道我昨天有面试？'
py -3.12 -X utf8 examples/experience_x1.py status --sandbox $x1
```

`day1` 创建新的 Soul 会话，从 Core 查询已接受的记忆并显示来源、World 和活动状态。`virtual_daily` 中 `PLAN` 表示作息来源；`PLANNED` 表示尚未发生；`ACTIVE` / `COMPLETED` 是合成时钟驱动的模拟状态，`inferred` 和 `reason` 指示推断，并不证明 Agent 真的去过那里。可以分别判断「事实找得对不对」和「世界状态是否可信」。因为没有模型接入，`--message` 目前只作为输入回显，不生成自然语言回答。

首次推进 Day 1 会先补算 Day 0 的散步，再推进到次日；昨天的活动为模拟完成，今天当前活动为 `UNKNOWN`，不会自动重复昨天作息。若试用 Hermes，现在在同一独立测试 Profile 中打开另一个全新会话，复制下列 Day 1 提示。它明确标注为手动传递的合成上下文；Hermes 不会自动访问本地 X1 状态，也不应复用主 Profile：

```powershell
py -3.12 -X utf8 examples/experience_x1.py hermes-prompt --day 0 --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py hermes-prompt --day 1 --sandbox $x1
```

Day 1 可用 `--message '你怎么知道我昨天有面试？'` 换问法。执行 `forget` 后再次生成 Day 1 提示，应不含已忘正文。只复制命令输出中的合成文本，不复制真实聊天或现有 Hermes 记忆。此试验只能评估给定事实后的语言表现，不能作为自动记忆接线、真实 Host 或 Soul Continuity 的通过证据。

负例和清理：

```powershell
py -3.12 -X utf8 examples/experience_x1.py isolation-check --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py forget --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py day1 --sandbox $x1
py -3.12 -X utf8 examples/experience_x1.py reset --sandbox $x1
```

`isolation-check` 在独立 RP World 写入合成密语，检查 Soul 正常检索不泄漏；`forget` 后再次打开会话，应看不到面试正文。`reset` 仅接受带 X1 标记、位于系统临时目录内的实例，删除该合成实例。

可选角色卡预览不会创建 World 或记忆；只在用户指定 `--card` 路径时读取该文件，输出不可信 profile 和 lore 条目数：

```powershell
py -3.12 -X utf8 examples/experience_x1.py card-preview --card '你的角色卡文件路径'
```

试用反馈请分别记录：C01 是否跨窗口记得、是否在合适时机提及；C04 是否能分清已发生和计划；最突兀的一句或最想补的世界细节。C03 已忘正文再次出现、C07 RP 内容混入 Soul 或活动被当成人类真实经历，均按阻断问题处理。样机不签发 M1 连续性或真实 Host 验收。
