# SP-004A ADR-003 — Character Definition vs Character Instance

## Status

Implemented candidate / PENDING_INDEPENDENT_REVIEW，2026-09-16。

## Context

PR #3 的 card_id 同时承担角色定义与历史记忆归属。同一张卡在两个世界的关系和剧情不应互相覆盖。

## Decision

CharacterDefinition 是不可变版本化定义，CharacterInstance 是绑定 owner/world/timeline 的独立实例。实例引用固定 DefinitionRef（ID + version），不按名称匹配。状态和关系的最小样本采用不可变 Values，拒绝共享 mutable dict/list。

SillyTavern V3 是未来 Import Adapter 的输入，经过 Versioned IR 映射到定义；核心不保存外部 JSON Schema 作为领域模型。未来 V4 或其他格式可新增映射器，不改变 World 身份边界。

## Consequences

旧定义升级不能改历史实例；只有 Owner 明确采用新版本才改变引用。此处未实现定义版本仓库、Importer、关系算法或迁移。完整定义字段由 D/G 扩展，保持版本与 owner 不变式。

## Verification

[Domain tests](../../../tests/test_domain.py) 验证一个定义对应两个世界实例、版本固定、错误版本拒绝、不可变状态以及跨世界引用拒绝。见 [Domain Model](../SP-004A-WORLD-DOMAIN-MODEL.md)。
