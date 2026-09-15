# SP-004A ADR-001 — Soul World as World

## Status

Implemented candidate / PENDING_INDEPENDENT_REVIEW，2026-09-16。仅 SP-004A 获准实施；Merge 未授权。

## Context

Soul 与角色身份需要不同生命周期，但所有权、来源、世界 ID 和隔离语义相同。建立两个 Runtime 会导致重复的权限与迁移逻辑。

## Decision

SoulWorld IS-A World。使用统一不可变 World 和 WorldKind，默认 Soul World 绑定 Soul 预留 ID。Roleplay 生命周期可挂起与归档；默认 Soul World 的关闭会话不停止其生活世界，普通角色世界命令不能删除或归档它。

## Consequences

统一模型不共享状态或权限，不把模拟生活变成现实事实。不新建 SoulRuntime 或 RoleplayRuntime。账户删除和后台时钟服务未实现，恢复策略留给后续阶段。

## Verification

[Domain tests](../../../tests/test_domain.py) 中 `test_soul_is_world_but_has_distinct_policy` 和双世界验收覆盖统一类型、默认 ID、生命周期差异。完整合同见 [Domain Model](../SP-004A-WORLD-DOMAIN-MODEL.md)。
