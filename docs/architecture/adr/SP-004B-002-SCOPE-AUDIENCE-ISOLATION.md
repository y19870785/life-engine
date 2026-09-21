# SP-004B-002 — Scope、Audience 与读取隔离

## 状态

SP-004B0 架构冻结候选 / PENDING_INDEPENDENT_REVIEW。固定 Base `4372b557dc8e3cc498098b6fe26e13df51ce802e`。不实现 ACL、查询或宿主适配。

## 背景

WorldScope 已定义 owner/soul/world/timeline，但构造它不证明这些对象存在或调用者有权访问。现有 Principal 是上游声明，WorldRepository 是受信内部接口。未来必须在检索、直接 ID、缓存、导出和 Prompt 入口使用同一授权合同，不能只保护最终文本。

## 决策

### 一、统一模型与基础边界

Soul 与 Roleplay 使用统一 MemoryRecord，每条绑定完整非空 WorldScope。服务从权威 World/Timeline 核对四元一致，不能信任请求 self-declared owner。首版每 World 一个 Timeline；所谓 world-level 公共知识是该 Timeline 内的 WORLD audience，timeline-level 明确归这条时间线，character-instance-level 由同域实例受众表达。没有无时间线记录、通配查询或跨分支继承。

same model != shared access。Soul ↔ Roleplay、同 Soul 的两个 Roleplay World 均默认不能互读。管理工具也必须显式选择一个 Scope；不能因 Owner 相同把当前角色查询自动改为所有世界查询。跨 owner 共享不属于本合同。

### 二、可信读取上下文

逻辑输入包含 authenticated Principal、已验证 WorldScope、用途、有效观看身份、请求查询/limit/投影字段与授权版本。用途为角色上下文、Soul 上下文或 Owner 管理/导出；观看身份恰好一个，不把同一个 Principal 控制的所有角色受众做并集。

角色上下文的观看身份由存储内当前 OPEN SessionBinding 的 character_instance_id 确定；Soul 上下文必须绑定 Soul World。两者均检查当前代次和绑定有效性，不能用请求字符串切换成 Owner 视图。Owner 管理操作需要单独明确授权，可在指定 Scope 查看自己的私有记录；结果只能交管理通道，不得流入角色 Prompt。

角色读取默认要求 ACTIVE 当前绑定；SUSPENDED/ARCHIVED 只允许 Owner 管理查阅，TOMBSTONED 普通读写拒绝，仅最小审计/删除维护例外。Owner 可在 CREATED/SUSPENDED/ARCHIVED 管理候选和删除，不因此推进 Story 或开放角色写入。当前没有归档应用入口不意味着 B0 新增了它。

### 三、Audience 的类型与含义

受众是非空、去重、顺序规范化的类型化集合；不能永久采用任意字符串。集合内是可见性并集，但始终再与调用者的 Scope、用途、身份及有效授权相交。WORLD 不与其他项混用，避免误以为加上私有项会限制 WORLD。

| 逻辑受众 | 语义 | 约束 |
| --- | --- | --- |
| WORLD | 当前 Timeline 中全部有效参与实体的公共知识，包括未来在此 Timeline 建立的实例 | 不表示互联网公开，不含其他 World；显式 Owner 批准，默认不采用 |
| CHARACTER_INSTANCE(id) | 指定实例的角色视角可用 | ID 必须存在且属于精确 Scope；不是 Definition ID |
| 多个 CHARACTER_INSTANCE | 这些实例共享而非全世界共享 | 例 A/B 集合不允许 C；写入者不能擅自扩大名单 |
| USER(owner_id) | Owner 的人类管理/用户视图可见，角色不可用 | 即使角色会话 Principal 属于该 Owner，也不匹配 USER 用途 |
| SOUL(soul_id) | 此 Scope 中 Soul 视角可用 | 仅允许在该 Soul 的默认 Soul World 内声明；Roleplay 中声明 SOUL 不能制造跨域 |
| PRINCIPAL(principal_id) | 指定受信主体的显式用户/管理用途 | 必须与 owner 关联、受信登记且操作授权通过；不是主体控制的所有角色都获得知识 |

B1 不提供多人共享服务；额外 Principal 未有可信登记/授权验证器时拒绝该受众，不按 UUID 猜测登记。新的实体类型也须先有同域解析器，否则拒绝，而不是通用字符串直通。

角色候选创建默认 CHARACTER_INSTANCE(当前绑定实例)，Soul 候选默认 SOUL(当前 Soul)；Owner 创建必须显式选择受众。角色不能扩大受众或为其他角色私有区写入。已有资料的派生默认取来源可见身份的交集，不因新记录作者是 Owner 而自动扩大；显式扩大需 Owner 对披露范围的独立批准。

实例不存在时拒绝新受众引用；将来实例 tombstone 后其匹配资格失效，原受众 ID 作为不可复用历史引用保留，不回退 WORLD/Definition/同名角色。共享集合可仍被其他有效成员读取；如果没有有效成员则仅 Owner 管理可见。存在性和删除状态检查必须在读写授权时执行，不能只依赖创建时检查。

### 四、Subject 不授予权限

subject 表示关于谁/什么，audience 表示谁可使用。`subject=A, audience=B` 表示 B 知道关于 A 的事，不意味着 A 能读。subject 的实体引用需要同域存在性校验，不允许用源引用偷偷读取另一个 World；跨域来源只能作为 F 审核的 lineage，不能直接跟随取正文。

### 五、查询与直接 ID

先验证主体/Scope/用途/受众，再构造授权候选集合，再进行检索、排名、limit、分页和计数。FTS 统计或向量排名也不能在全库计算后截断过滤，避免隐藏数据影响候选及分数。无合格分区或预过滤能力的索引不可上线；可退回同样限域的 canonical 查询。

get_memory(memory_id) 的逻辑输入必须同时含 authenticated Principal、authorized WorldScope 和观看上下文；限域定位后仍查受众、删除/来源撤销和版本。不得先查全库再提示“这个 ID 在另一个世界”。服务对外统一返回不可用，不区分不存在/无权/已隐藏；存储损坏、锁超时则是基础设施错误，不伪装成不可用记录。详细权限审计只在 Owner 管理通道可见，不含不必要正文。

ID 解析有效也不是授权。批量读取逐项遵循同规则，不泄漏隐藏记录计数；查询计数、排序、分页游标、错误和耗时预算不能显式依赖未授权候选。共享资源的计时侧信道不承诺完全消除。

### 六、缓存、导出、备份与诊断

缓存命中前重新验证授权，命中后也核对安全版本。namespace 至少含安装/数据代次、Owner/Soul/World/Timeline、Principal、观看身份、用途、audience 授权摘要、政策/撤销版本、Memory revision、IndexGeneration，以及 query/limit/排序/字段/过滤/游标。细则见 [ADR-003](SP-004B-003-REVISION-QUERY-CACHE.md)。不得以角色名、Definition、embedding 或 query 独立为键。

普通 export 与 debug dump 是读操作：同样限域、限受众和字段最小化。Owner 专用管理导出可读指定 Scope 的完整授权历史，但必须显式选择，不得从角色工具触发。分页导出固定一致版本，期间授权撤销则停止并废弃未交付部分；不能声称能收回此前已交给用户的字节。

durable backup 是安装 Owner 的显式灾备操作，授权范围可覆盖所选实例所有 World，是独立管理权限，不是角色 audience 的隐式例外。备份文件属于私有数据，按受信目录/文件权限保存，不暴露为 MemoryQueryResult，也不放入匿名报告。restore 必须通过删除/撤销门禁，不能利用备份作为越权读接口。

匿名诊断只输出固定错误分类和必要统计，不含 Memory 正文、私有来源 prompt、查询文本、原始 ID/路径或可反查源的内容指纹。兼容性报告不能直接序列化 MemoryRecord。日志和索引同样是敏感资产，不能因“调试”默认扩大读取权。

### 七、Bridge 与 Prompt

未来 K 只消费已经授权且投影过的 MemoryQueryResult，包含必要 reality/canon 标签及经过授权的来源摘要，不取得裸表访问权。结果是数据，不是模型指令；原始 lineage/source 引用的正文另行授权，不能递归解引用。Prompt 不是权限系统。

F 才可跨域创建新的目标记录，保留 source Scope、memory/event、grant reference/version、transformation 和 RealityStatus；不能修改源 world_id。许可不可传递，Roleplay → Soul 的 FICTIONAL_SHARED_EXPERIENCE 不成为现实旅行等事实。EXIT/SUSPEND/summary/aside 没有跨域权限。

H 若不能证明 stable principal/session、message provenance、isolated context lane 与 history isolation 为 SUPPORTED，应按 A 合同拒绝私密上下文服务或明确降级为不读取私密记忆的模式，不能以 Memory 服务安全宣称整个宿主强隔离。B0 不实施宿主适配。

## 攻击与误用验证

| 案例 | 为什么被阻断 |
| --- | --- |
| B World 提交 A 的 memory UUID | B Scope 内候选不存在，不能按全局 UUID 绕过读取 |
| A/B 共用 X@1，按 definition_id 找记忆 | Definition 不是权限/分区键；实例与 Scope 必须不同 |
| A 主体把 audience 改成 WORLD | 会话只能写自身私有候选，扩大受众需 Owner 批准 |
| 同一 Owner 的角色 A 要求 USER 私密记录 | 有效观看身份是 A，不能匹配 USER 管理用途 |
| 相同查询缓存命中另一角色结果 | namespace 包含观看身份、受众摘要及安全版本 |
| subject=A 因而 A 读取 audience=B | subject 不进入授予条件 |
| 删除实例后新建同名实例 | ID 不复用，名字不匹配历史受众 |

## 备选方案与拒绝项

拒绝同卡共享、memory_type 区分权限、缺 Scope 就全库搜索、查询后过滤、Owner 身份在任意 Prompt 中全权读取，以及任意 audience 字符串充当永久 ACL。类型化 audience 增加校验成本，但使单角色和用户视角可验证；未实现的身份解析一律拒绝。

## 影响

授权与内容检索是两个步骤，基础仓储只能给受信服务调用。Owner 管理能力与角色视角分离，避免混淆代理人权限；公开到 WORLD 包括未来实例，是显式披露决定。无法隔离的外部索引或宿主不能消除该边界。

## 验证要求

未来测试至少覆盖上述攻击、Soul/Roleplay 两向默认拒绝、直接/批量 ID、导出/分页、来源引用、同查询跨主体缓存、实例 tombstone，以及撤销发生在返回前的竞争。当前 [domain_policy.py](../../../runtime/life_engine/domain_policy.py) 只是前置策略合同，不能称为现成 Memory ACL。

## 后续工作

B1 实现受信服务合同和 Owner/会话最小权限；F/H 分别实现 Bridge 与宿主能力验证。相关：[主架构](../SP-004B-WORLD-MEMORY.md)、[语义](SP-004B-001-MEMORY-SEMANTICS.md)。
