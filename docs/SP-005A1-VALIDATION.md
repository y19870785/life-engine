# SP-005A1 自动验证映射

固定 Base：`9159c493ad435cf947ed8c0fef278e1f5fb9dc83`。此表映射 [A0 + R1 的 48 项验收](planning/SP-005A1-TEST-MATRIX.md)，自动测试不是独立审核或真实 Host PASS。测试使用临时安装、显式 SOUL World、受控时钟与独立子进程，不接生产 Host。

## 逐项映射

| 编号 | 具体测试 |
| --- | --- |
| T01 | [test_t01_midnight_local_budget_and_rolling](../tests/test_living_runtime.py)；[test_t09_t10_dst_day_and_gap_fold](../tests/test_living_runtime.py) |
| T02 | [test_t02_t03_fresh_process_activity_window](../tests/test_living_runtime.py) |
| T03 | [test_t02_t03_fresh_process_activity_window](../tests/test_living_runtime.py) |
| T04 | [test_t04_missed_activity_not_fabricated](../tests/test_living_runtime.py) |
| T05 | [test_t05_active_completion](../tests/test_living_runtime.py) |
| T06 | [test_t06_backlog_128_and_long_stop](../tests/test_living_runtime.py)；[test_t06_deterministic_recovery_partitions](../tests/test_living_runtime.py) |
| T07 | [test_t07_t13_same_time_activity_and_overlap](../tests/test_living_runtime.py) |
| T08 | [test_t08_timezone_change_cancels_unclaimed](../tests/test_living_runtime.py)；[test_t01_midnight_local_budget_and_rolling](../tests/test_living_runtime.py) |
| T09 | [test_t09_t10_dst_day_and_gap_fold](../tests/test_living_runtime.py) |
| T10 | [test_t09_t10_dst_day_and_gap_fold](../tests/test_living_runtime.py) |
| T11 | [test_t11_t12_tzdata_clock_regression](../tests/test_living_runtime.py)；[test_t11_tzdata_change_requires_explicit_policy](../tests/test_living_runtime.py) |
| T12 | [test_t11_t12_tzdata_clock_regression](../tests/test_living_runtime.py) |
| T13 | [test_t07_t13_same_time_activity_and_overlap](../tests/test_living_runtime.py)；[test_t13_spontaneous_choice_persisted](../tests/test_living_runtime.py)；[test_t13_activity_recreate_cancelled_window](../tests/test_living_runtime.py) |
| T14 | [test_t14_observation_expiry_and_special_date](../tests/test_living_runtime.py) |
| C01 | [test_c01_c05_c07_decision_followup_idempotency](../tests/test_living_runtime.py) |
| C02 | [test_c02_quiet_boundary](../tests/test_living_runtime.py) |
| C03 | [test_c03_combined_blockers_and_verified_outbound](../tests/test_living_runtime.py) |
| C04 | [test_p01_p02_two_process_quota](../tests/test_living_runtime.py)；[test_c17_quiet_execution_cancels_without_refund](../tests/test_living_runtime.py)；[test_t01_midnight_local_budget_and_rolling](../tests/test_living_runtime.py) |
| C05 | [test_c01_c05_c07_decision_followup_idempotency](../tests/test_living_runtime.py)；[test_c05_pause_suppression_retains_opportunity](../tests/test_living_runtime.py) |
| C06 | [test_c18_inbound_cancels_and_new_reservation](../tests/test_living_runtime.py) |
| C07 | [test_c01_c05_c07_decision_followup_idempotency](../tests/test_living_runtime.py)；[test_c08_c09_verified_fake_delivery_only](../tests/test_living_runtime.py) |
| C08 | [test_p05_claimed_crash_unknown_no_retry](../tests/test_living_runtime.py)；[test_c08_c09_verified_fake_delivery_only](../tests/test_living_runtime.py) |
| C09 | [test_c08_c09_verified_fake_delivery_only](../tests/test_living_runtime.py) |
| C10 | [test_c10_assistant_only_explicit_followup](../tests/test_living_runtime.py) |
| C11 | [test_c11_c12_media_opportunities_no_jobs](../tests/test_living_runtime.py)；[test_c11_media_budget_expiry](../tests/test_living_runtime.py)；[test_c11_photo_cancel_tracks_activity](../tests/test_living_runtime.py) |
| C12 | [test_c11_c12_media_opportunities_no_jobs](../tests/test_living_runtime.py) |
| C13 | [test_c13_last_quota_execution](../tests/test_living_runtime.py) |
| C14 | [test_c14_no_self_cooldown](../tests/test_living_runtime.py) |
| C15 | [test_c15_other_intent_still_cooldown](../tests/test_living_runtime.py)；[test_c01_c05_c07_decision_followup_idempotency](../tests/test_living_runtime.py) |
| C16 | [test_c16_policy_lower_cap_raise_spacing](../tests/test_living_runtime.py)；[test_c16_each_reservation_rule_change](../tests/test_living_runtime.py) |
| C17 | [test_c17_quiet_execution_cancels_without_refund](../tests/test_living_runtime.py)；[test_c17_c18_expired_intent_never_reopens](../tests/test_living_runtime.py) |
| C18 | [test_c18_inbound_cancels_and_new_reservation](../tests/test_living_runtime.py)；[test_c17_c18_expired_intent_never_reopens](../tests/test_living_runtime.py)；[test_c18_reopened_opportunity_two_processes](../tests/test_living_runtime.py) |
| P01 | [test_p01_p02_two_process_quota](../tests/test_living_runtime.py) |
| P02 | [test_p01_p02_two_process_quota](../tests/test_living_runtime.py) |
| P03 | [test_p03_operation_revision_generation_conflicts](../tests/test_living_runtime.py) |
| P04 | [test_p04_crash_before_inside_after_commit](../tests/test_living_runtime.py) |
| P05 | [test_p05_claimed_crash_unknown_no_retry](../tests/test_living_runtime.py)；[test_p05_send_before_db_result](../tests/test_living_runtime.py) |
| P06 | [test_p06_p07_persisted_choice_across_processes](../tests/test_living_runtime.py)；[test_p06_independent_choice_order](../tests/test_living_runtime.py) |
| P07 | [test_p06_p07_persisted_choice_across_processes](../tests/test_living_runtime.py) |
| P08 | [test_p08_restore_generation_fence](../tests/test_living_runtime.py) |
| P09 | [test_p09_corruption_fail_closed](../tests/test_living_runtime.py)；[test_p09_doctor_structural_corruption_matrix](../tests/test_living_runtime.py) |
| P10 | [test_p10_scope_and_closed_world_fail_closed](../tests/test_living_runtime.py)；[test_p10_scope_race_same_sqlite_transaction](../tests/test_living_runtime.py) |
| P11 | [test_p11_snapshot_bound_readonly_revalidation](../tests/test_living_runtime.py) |
| P12 | [test_p12_activities_do_not_write_other_domains](../tests/test_living_runtime.py)；[test_owner_accept_idempotency_correction_and_restart](../tests/test_story_runtime.py) |
| P13 | [test_p13_copy_all_rows_and_empty_enrollment](../tests/test_schema8_migration.py)；[test_p13_second_instance_failure_keeps_registry](../tests/test_schema8_migration.py) |
| P14 | [test_p14_handoff_preserves_and_fences](../tests/test_living_runtime.py) |
| P15 | [test_p15_verified_backup_old_release_rollback](../tests/test_schema8_migration.py) |
| P16 | [test_p16_schema8_legacy_until_enrollment](../tests/test_living_runtime.py) |

## 证据边界

P07 验证新 Core 进程与重复调用不会重建计划，复用既有模拟插件 reload 合同；不表示真实 Hermes/OpenClaw restart。P09 在事务内注入 FK、subject、epoch、日志、choice、receipt 损坏后回滚测试副本；运行时不自动修库。P12 复用 Story 的 Owner 明确接纳、幂等与重启测试，Living 不直接向 Story/Memory/Lore 双写。

DST 使用 [TZif fixture](../tests/living_time_fixture.py) 固定 2026 年 gap/fold 转换；fixture 不安装到生产，生产具名时区需要实际 IANA 数据。P04/P05 的 [进程助手](../tests/living_process_fixture.py) 用 os._exit 模拟未提交、已提交、CLAIMED 和模拟 send 后崩溃；模拟 send 只写临时文件，绝非真实渠道发送。

最终测试数量、CI Head 和运行记录见 [验证记录](VALIDATION.md)。
