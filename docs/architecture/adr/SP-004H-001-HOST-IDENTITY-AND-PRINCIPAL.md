# ADR SP-004H-001 — Host Identity and Principal

状态：H0 架构冻结候选；固定 Base `68c24b010ee464a66e0e853ab50f85b7e861e148`。参见[主合同](../SP-004H-HOST-INTEGRATION.md)。

## 决策

`TrustedHostAdapter` 将受信 HostInstallation、HostAgent/Profile、HostConversation 和已认证 HostUser/Sender 分别识别，再用 `HostPrincipalKey(adapter, host_instance, host_profile_or_agent, authenticated_user_identity)` 映射到 Life Engine `Principal`。首版每个 Life Engine instance 只支持一个可信 Owner。Host ID 只是映射材料，不直接作为 `DomainId`；Host chat 不是 World，sender 字符串不是 Principal。Principal 只能由受信适配代码声明，且每次操作仍须由 World/Bridge Runtime 验当前 owner、Scope 与 Session。Host workspace/profile 路径是绑定证据，不是身份或凭据。映射在 reload/reconnect 后重新核验；同一认证用户应稳定，其他用户、agent/profile 必须分离。

仅认证的 `EXTERNAL_USER` 事件可携 Owner command；assistant、tool、automation、host notice 或未知来源文本无权建立 Principal 或执行 ENTER/SWITCH/Bridge confirm/revoke。Nested/delegated/child-agent 首版默认拒绝 Owner action，未来委托需独立合同。不能从 prompt 中的“我是主人”推断身份。现有 `Principal` 是受信声明而非登录凭据；此 ADR 不修改其领域类型。

## 理由与后果

宿主 conversation 可切换 World，同一 World 可跨宿主 run；把任一 Host 标识直接当领域主键会把传输生命周期误作真源。Adapter 必须在目标 Host 版本实测认证与稳定性，不能因 hook 提供 `sender_id` 就宣布身份可信。H1/H2 可以选不同的 Host 认证接口，但输出相同映射与拒绝语义。H0 不实现映射持久层或多人协作。
