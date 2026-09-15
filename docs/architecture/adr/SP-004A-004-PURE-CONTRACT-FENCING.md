# SP-004A ADR-004 — Pure Contracts and Writer Fencing

## Status

Implemented candidate / PENDING_INDEPENDENT_REVIEW，2026-09-16。

## Context

任务要求验证旧会话结果失效，但不授权 lease manager、正式持久化或宿主接入。只有类型声明不能证明 fencing，直接写数据库则越界。

## Decision

提供纯 lifecycle reducer、binding 构造与 validate_write：对照当前 World 的 revision/epoch、scope 和 principal，拒绝旧绑定。状态转换递增两个计数；close_session 失效旧代，SWITCH 只关闭源世界。采用保守单 writer/最后参与者合同，epoch 在 World 级生效。

桥接合同仅作当前 grant 的资格判断，默认 deny；宿主能力必须显式 supported。许可和能力枚举禁止隐式 bool 转换。

## Consequences

纯函数无法察觉调用方提供的是旧 World。未来 B/H 必须提供可信身份、最新快照与原子 CAS，之后才可声称并发持久安全。不得把当前函数注册为未认证的生产写接口。缺少 grant 存储/撤销/lineage 或宿主真实隔离时，不得以通过纯测试代替服务验收。

## Verification

[Domain tests](../../../tests/test_domain.py) 覆盖退出、切换、挂起、恢复后的旧 epoch 拒绝；stale revision、跨 principal、封闭 session 拒绝；桥接字段/方向/有效期/撤销和 capability 降级检查。见 [Domain Model](../SP-004A-WORLD-DOMAIN-MODEL.md)。
