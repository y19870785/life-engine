# X2-A 真实模型最小试用合同候选

当前许可只见 [STATUS](../STATUS.md)。本合同独立于 [L1 离线实施](LE-RESET-01-X2-A-L1-IMPLEMENTATION-PROPOSAL.md) 和本机已有 Hermes 专项许可。本文不读取凭据、不探测端点、不发送请求；没有真实模型结果。

## 先把未确定的目标写清楚

当前 Review 没有指定 X2 的 provider、准确端点、模型或凭据引用。为了不擅读生产 Hermes/.env 或替用户选择账户，本轮没有从生产配置中补这些值。已向用户请求“端点 + 模型名 + 凭据引用名，或仅离线”；未收到配置不解释为同意。

下面给出完整的最小配置、预算和校验门。**其中目标字段必须由用户明确补齐并批准；它现在不是可执行配置，也不能称为模型试用已具备条件。**

```json
{
  "authorization_id": "X2-A-L2-SMOKE-01",
  "approved_head": "TO_APPROVE_AFTER_L1_REVIEW",
  "package_sha256": "TO_APPROVE",
  "fixture_id": "ONE_NEW_SYNTHETIC_FIXTURE_TO_APPROVE",
  "endpoint": "EXACT_HTTPS_ORIGIN_AND_PATH_TO_APPROVE",
  "model": "EXACT_MODEL_ID_TO_APPROVE",
  "credential_ref": "env:X2_MODEL_API_KEY",
  "data_scope": "X2_SYNTHETIC_ONLY",
  "sessions_max": 2,
  "requests_per_session_max": 4,
  "requests_total_max": 6,
  "input_tokens_per_request_max": 2048,
  "output_tokens_per_request_max": 256,
  "input_tokens_total_max": 12288,
  "output_tokens_total_max": 1536,
  "request_body_utf8_bytes_max": 16384,
  "cost_currency": "USD",
  "cost_total_max_microunits": 1000000,
  "automatic_retries": 0,
  "redirects": 0,
  "streaming": false,
  "tools": false,
  "expires_after_first_request_hours": 24
}
```

建议首轮只做 **6 请求 / 2 会话 / 24 小时 / 总费用最多 USD 1.00** 的冒烟。费用是拟定硬预算，不是价格估算或消费承诺；provider 若不按 USD 计费，需要另定币种与同币种上限，不默算汇率。先前七天28请求是长期观察建议，本合同不继承；扩展到一周须另批剩余额度，不能自动续额。

两次合成 RP 问答为会话一的2请求；会话二最多4请求，用于明确追问、自然提及、无关问题与未知细节。失败或未知结果也占额度，因此实际可观察场景可能不足六项，按实际记录，不自动补发。

## 请求和费用必须能硬限制，不能只配置一个数字

实施 L2 前需为用户选定端点单独核官方协议/模型支持与价格证据，固定其版本、日期、计量项和 hash。最小 adapter 用标准库单次 REST，禁 SDK 自动重试、fallback、标题/摘要/embedding 辅助模型调用、工具调用和流式响应；如果真实接口会引入未计量请求或无法约束账单项，不进入实测。

输入 token 数必须由该模型经过验证的离线计数方式得出，包含系统边界、role、回忆包与当前输入；**不能用字符数/字节数冒充 token 精确计数**。暂无该端点的可靠计数方案时，该门保持 `TOKEN_BOUND_NOT_PROVEN`，不调用。若 tokenizer 实现要求新第三方运行依赖，超出 L1 和本最小合同，先单独决策，不能静默安装。

输出必须有目标端点实际强制的256 token上限，包含所有可计费输出/内部推理项；无法证明时停在 `OUTPUT_BOUND_NOT_PROVEN`。对不支持该硬限或存在未计入隐式推理/额外费用的模型，不靠改小提示“尽量简短”通过。body UTF-8 16,384 bytes 是独立资源上限，不是 token 替代。

费用账本以同币种整数 micro-unit 计量。每次发送前按已批准的价格表，保守预留本次最大 input/output token 费用和所有固定附加项；累计预留不得超过1,000,000 micro-USD。不使用可能命中的缓存折扣降低预留，不凭未知usage退款。价格/计量项未知、价格到期或新增收费项即拒绝。若计价模型不能由上述有限上界覆盖，须由 provider 侧可核验硬预算或新的具体合同补齐，不能声称客户端已保证总费用。

## 计数与网络边界

唯一模型网络出口在 L2 adapter，调用者不能传 URL、key、headers、model 或 retry 参数。URL 无 userinfo/query 中凭据/fragment，精确 HTTPS origin/path，TLS 校验开启、重定向关闭，不使用继承的代理环境，不读取生产SDK/配置。未知provider/model或合同摘要不匹配时无请求。L1完全不构造此出口。

预算账本由该 authorization 统一持有，置于业务 fixture 的快照/重置范围之外；每次请求前持锁写入并持久化 reservation，再发一次 HTTP。新会话、新 fixture、重开进程都不归零。账本丢失/损坏/identity不符停止，不创建新的零预算账本继续。超时、断连、usage未知按已消耗预留处理，无自动重试；用户显式重试也必须新 reservation 并受同总限。

这能约束受审应用的所有模型调用，不声称抵御同 OS 用户篡改账本或 provider 账单行为。验收必须用本地 fake HTTP 服务器实际证明重开、并发、第七次请求、超限token/费用、网络未知结果、隐藏辅助调用与重定向路径零越界；只有这些离线门和精确实现独审通过后才执行一次获准真模型冒烟。

## 凭据、数据与结果

`env:X2_MODEL_API_KEY` 只是建议引用名称。批准后用户在该次 X2 进程环境中显式提供，代理只读这一引用，不搜索文件或遍历环境；不接收用户把密钥贴到对话。缺失引用即禁用，不 fallback 到 Hermes、默认账户或其他 provider。秘密不写包/日志/页面/导出，也不把原始认证失败body回显。

仅发同一新 fixture 的合成卡片、合成输入及已接受的虚构回忆录；不读微信/Telegram/Hermes历史、不发真实人物资料、照片或生产文件。不接 Host、不启动 Gateway、不发渠道消息；模型 HTTP 请求与渠道 `REAL_SEND` 是不同权限，不能互相推导。

保存实际请求次数、预算预留、脱敏阶段/usage、检索ID、输入版本和用户观察。模型回答仍是候选；不因说“我记得”通过底层验收。泄漏、跨World、未知预算、秘密进日志、模型替换或包漂移立即停用出口，保留脱敏证据，不自动修生产。

## 用户最少需要批准什么

1. 是否先批准 L1 离线实施；它不需要提供任何密钥或模型配置。
2. 若还要批准后续真实模型冒烟：指定**准确 endpoint、model、credential_ref 名称**，确认上述六请求/token/24小时/费用预算，或提出替代上限；只能在 L1/L2具体实现独审与硬限证据完成后执行。
3. 精确试用 Head/包与新 fixture 的绑定在发布时补齐；未绑定不能用本合同任意替换新版本。批准这份候选不授权生产 Hermes、迁移、渠道、Ready 或 merge。

如果用户本轮只回复“仅离线”，保留本合同为将来提案，不能把它作为 L2 授权。目标字段和可行的 token/费用计量闭包未补齐前，即使用户认可“试模型方向”，也只说明规划意向，不允许实际调用。
