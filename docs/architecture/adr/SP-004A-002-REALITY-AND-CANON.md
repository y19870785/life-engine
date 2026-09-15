# SP-004A ADR-002 — Reality and Canon Are Orthogonal

## Status

Implemented candidate / PENDING_INDEPENDENT_REVIEW，2026-09-16。

## Context

现实陈述可能未经核实，虚构事件可能是明确接受的世界历史。一个 is_real 布尔值无法同时描述信息来源和是否进入既定状态。

## Decision

分离 RealityStatus 与 CanonStatus。支持观测、用户陈述、Agent 推断、模拟生活、虚构、虚构共同体验、unknown 与 legacy_unreviewed；Canon 独立采用 candidate/accepted/rejected/unreviewed。Provenance 默认 candidate。用户报告/模型/模拟来源不能声明观测事实；接受不改变 reality。

## Consequences

candidate_event 不是 RealityStatus。本阶段值构造允许调用方显式提供 accepted，但不执行批准流程；后续服务必须验证谁有权接受。观测和 bridge 标签只是上游断言，不能替代证据与 lineage 审核。禁止用 scope=soul 代表事实为真。

## Verification

[Domain tests](../../../tests/test_domain.py) 中 reality/canon 独立性、候选默认值和虚假观测来源拒绝检查。完整字段见 [Domain Model](../SP-004A-WORLD-DOMAIN-MODEL.md)。
