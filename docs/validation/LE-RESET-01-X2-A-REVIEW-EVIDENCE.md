# X2-A 定向复核证据台账

当前状态只见 [STATUS](../STATUS.md)。本轮执行日期 2026-10-24（Asia/Shanghai）。只做 PR #64 Review 续办：本机候选差异、Core组合、L1实施范围与L2模型门，不重复全仓审计。

## 固定对象与审查来源

- 远端 main 与候选 diff Base：`baa59729babf9ac56a17e02c682de2e3086e3575`。
- PR续办前 Head：`f4bf7b5804c06eb0c50867d42b88f2fcaf79baa6`，Draft/open；OWNER [Review 5631726989](https://github.com/y19870785/life-engine/pull/64#pullrequestreview-5631726989) 是 COMMENTED，不是 APPROVE。
- 旧Head精确PR CI [39976791743](https://github.com/y19870785/life-engine/actions/runs/39976791743) 四矩阵 success 已核验；新文档Head的CI独立记录在PR，不继承旧绿。
- 新冻结 C2 UTC：`2026-10-24T01:31:00.855371+00:00`；manifest原始字节SHA256 `045ed49ac08ead503df47133ae669810766abcce2ce666bb5ed693ac669abc02`。187个runtime/integrations/tools/tests/examples源码与fixture文件；根入口来自固定Base，另核实其来源。43个有语义diff，相关37个、旁线6个，均与main逐文件比较。
- C2是WORKING_TREE_UNCOMMITTED，非干净main；代码仅复制至新建系统临时目录。运行用独立detached临时worktree保留迁移测试所需Git历史，覆盖187个冻结文件；不在原工作树执行，不读取真实Host/密钥/聊天。

## 远端可读完整相关diff

| 附件 | 内容与完整性 |
| --- | --- |
| [CORE-DIFF](evidence/LE-RESET-01-X2-A/CORE-DIFF.md) | 5个相关Runtime文件的全部差异，含后来不进入L1的scan/Prompt部分 |
| [PROVIDER-TOOLS-DIFF](evidence/LE-RESET-01-X2-A/PROVIDER-TOOLS-DIFF.md) | 8个provider/工具/示例的全部新增文本 |
| [TESTS-DIFF](evidence/LE-RESET-01-X2-A/TESTS-DIFF.md) | 24个相关测试/语料文件全部新增文本 |
| [MINIMAL-CORE-PROJECTION](evidence/LE-RESET-01-X2-A/MINIMAL-CORE-PROJECTION.md) | L1拟采用的三文件精确最小投影；剔除无关变更 |
| [REPRO-PROBES](evidence/LE-RESET-01-X2-A/REPRO-PROBES.md) | 本轮合成反例、最小投影构造器、实际Core新进程证明和92项命令 |

这些都是Markdown证据，不能因在文档中出现代码就认定产品已实现/已部署；本PR没有修改Runtime或测试文件。完整相关diff不省略正文或断言；统一LF的unified diff与raw字节SHA分开，不能把原始CRLF hash当作git应用后的hash。

另6个旁线只有分类/摘要，不混入要复用的37文件；它们不属于候选准入闭包。C2全量包含这6个旁线，因此它是本机冻结对象的一次整体回归，不可替代三文件投影或未来X2的验收。远端重建最小对象可用投影diff和TESTS-DIFF中的test_roleplay_recall.py，不需要本机路径或私有运行回执。

根入口不在187文件清单中。三份入口来自固定main的工作树checkout，LF文本逐项一致；Windows autocrlf导致raw bytes可与Git blob不同，分别记录（不是从生产Host复制）：

| 根入口 | 运行树raw SHA256 | Git blob SHA256 |
| --- | --- | --- |
| `setup.py` | `903375a2e19358ef8fec34ebf69ce218bb6cb4857f8a5210b773b7c6d8b8e5e4` | `7cf595ef47493efdc583a4690706b98c02a2cb70644a6695964393ac356bda95` |
| `setup_legacy.py` | `01d011c5b46fe43fa72eecf84aa9d94c9e8003e4b1243f8b8e51385209a9fb2b` | `fab986ab48e176136d0db855515b281887b0b9052f36870ad5a0c8a910472429` |
| `life.py` | `fde2873f44421946335e6318f78fea6c28786962ca2418c40bd7005e0fb7c10c` | `16b8f81458ee17d3392c200438de0dfab791ba0d854000fee1ef50b3247d0546` |

## 逐项实际执行

环境：Windows-11-10.0.26200-SP0；Python 3.12.10；SQLite 3.49.1。未运行3.10，也不以本机结果替代Linux/3.11。命令使用Python3.12与UTF-8，所有业务数据是新临时合成fixture。

### E1：C2完整冻结候选全量

```powershell
$env:PYTHONUTF8='1'
py -3.12 -B -m unittest discover -s tests -q
```

<!-- C2_FULL_RESULT -->
本轮实际终态：`Ran 922 tests in 940.417s`，`OK (skipped=4)`，退出码 `0`。
完整本地日志 `le64-candidate-full.log` SHA256 为
`2bb6d64dac050ca0cc42d51e228f1dcc3d21aa861ac0360f8c22209fe2bea83f`。
quiet输出未列四项逐项skip原因，不猜测名单；仅在本次Windows/Python3.12环境取得结果，未跑C2的Linux/3.11。
<!-- /C2_FULL_RESULT -->

包含当前C2相关新增测试和旁线代码，不是X2产品测试。临时目录ResourceWarning不隐藏；跳过如实记录，不推断为通过。

### E2：三文件临时最小投影

只投影domain新枚举、memory_runtime必要安全闭包、roleplay_recall完整文件。scan/MemoryFailure新增码/Prompt/Host/provider完全未抽取。选择RoleplayRecallTests及原main的test_memory_runtime、test_memory_restore、test_bridge_runtime、test_prompt_runtime，**92 tests，119.617s，OK，0失败/错误/跳过**；进程退出0。原有拒绝断言未删改。

这验证该最小Core差异能通过现有安全回归；测试代码是审查fixture，产品尚未开工。投影diff SHA256 `0e5ebf19072dea44bf7be3b65f5ed568e886c3c89a8475584e2cdd8ad44c3077`。

### E3：Core真实调用与新进程读回

在E2对象上运行REPRO-PROBES中的core-path-proof：临时RP用户记录→create_session_candidate→RecallSource/record_recall(accept=False)→Soul查询空→显式accept_memory→关Core连接→新Python进程以新Soul Session查询。

```json
{
  "scope": "TEMP_CORE_PROJECTION_ONLY",
  "model_turn_canon": "candidate",
  "soul_before_accept_count": 0,
  "accept_created_successor": true,
  "new_process_exit": 0,
  "new_process": {
    "count": 1,
    "reality": [
      "fictional_shared_experience"
    ],
    "source": [
      "roleplay_recall"
    ],
    "expected_anchor_found": true
  },
  "real_model_requests": 0,
  "web_layer": "NOT_IMPLEMENTED"
}
```

不是mock Memory，不是模型回答；web_layer明确NOT_IMPLEMENTED。由此只能确认Core消费路径，不能预先判HTTP/UI/包隔离通过。

### E3B：唯一初始化子进程的隔离可行性

在E2对象上调用真实durable.create_install，审查用guard仅接收已核验的probe_release完整argv/脚本文字/Schema8/release路径；真实子进程加-I -S -B -X utf8、最小系统/临时目录环境，拒绝网络/孙进程audit事件。运行入口本身也用-I -S。

实际只启动一个子进程，退出0；isolated=1、no_site=1，memory_runtime实际导入路径在该fixture release内；环境无HOME/USERPROFILE，未导入agent/Hermes SDK。仅本fixture生成bridge参考文件，合成host/plugins不存在；错脚本、错Schema、错解释器三项均在执行前拒绝。

这证明既有初始化探针可在有限guard下运行，不是已实现的X2启动器，也不证明任意包/任意本地攻击者的隔离。探针全文已附REPRO-PROBES，仍须在实际L1实现中重验。

```json
{
  "scope": "TEMP_CORE_INITIALIZER_PROBE_ONLY",
  "real_child_count": 1,
  "child": {
    "isolated": 1,
    "no_site": 1,
    "home_in_env": false,
    "profile_in_env": false,
    "host_sdk_imported": false
  },
  "module_inside_release": true,
  "host_plugins_created": false,
  "bridge_reference_inside_fixture": true,
  "negative_checks": [
    {
      "id": "wrong_script",
      "denied": true
    },
    {
      "id": "wrong_schema",
      "denied": true
    },
    {
      "id": "wrong_python",
      "denied": true
    }
  ],
  "original_probe_body_sha256": "bd53cf99bcec4b24c80284df4a63371ccf4d245e9d72c16dda38a004a24ef705",
  "web_layer": "NOT_IMPLEMENTED",
  "real_model_requests": 0
}
```

### E4：provider重用边界的5个实际观察

运行REPRO-PROBES中的reuse-probes，在全新临时store分别观察available初始化、MODEL canon、默认flush、同basename映射和未知版本迁移。未读取真实Profile；未来version是人为合成负例，不表示生产文件已降级。

```json
{
  "scope": "LOCAL_SYNTHETIC_ONLY",
  "snapshot_manifest_sha256": "045ed49ac08ead503df47133ae669810766abcce2ce666bb5ed693ac669abc02",
  "probes": [
    {
      "id": "P01_AVAILABLE_INITIALIZES",
      "available": true,
      "before_root_exists": false,
      "after_state_exists": true
    },
    {
      "id": "P02_MODEL_TURN_CANON",
      "source": "model",
      "canon": "accepted",
      "reality": "fictional"
    },
    {
      "id": "P03_DEFAULT_FLUSH_ACCEPTS",
      "canon": "accepted"
    },
    {
      "id": "P04_BASENAME_ALIAS",
      "same_rp_scope": true,
      "two_profile_paths_different": true
    },
    {
      "id": "P05_UNKNOWN_VERSION_REWRITTEN",
      "input_version": 999,
      "output_version": 2,
      "future_field_retained": false
    }
  ],
  "real_model_requests": 0,
  "real_host_access": false
}
```

这些结果要求X2编排避开相应入口，不等于Core同Soul授权已被攻破；具体修订见候选复核。

### E5：C2当前质量评测

在C2冻结运行目录执行 `py -3.12 -B -X utf8 tools/roleplay_recall_eval.py`，退出0；execution COMPLETED、安全65次检查PASS，检索9/10 MET，paraphrase仍GAP，quality GAPS_OBSERVED；不升格为自然聊天通过。Unicode类别修补已经存在，不能沿用C1的未修状态。

semantic_sha256 `ab2b11c1e4d669e4e50ae49f6fd70e7ed81c297a60de565a2dde8f497962a7ba`。

### E6：静态与范围核对

<!-- REVIEW_STATIC_RESULT -->
本轮11份新增/修改Markdown的36个本地链接/锚点有效；180个候选Python文件AST解析通过；附件37文件diff还原可见空白行后，与C2按LF逐项重算一致；整组37文件与三文件投影均通过 `git apply --check`（只检查，不应用到PR工作树）。C2冻结目录、全量运行树与原工作树对应187文件均无hash漂移。最终暂存范围只含Markdown，不改任何产品代码/断言；`git diff --cached --check`通过；不新增或弱化产品断言。
<!-- /REVIEW_STATIC_RESULT -->

附件用 `␠` 显示diff里仅含一个ASCII空格的上下文行，避免Markdown本身出现行尾空白；抽出fenced patch后逐行还原，不改实际源码。还原方式为 `''.join(' \n' if line == '␠\n' else line for line in patch.splitlines(keepends=True))`。两套还原后的patch已实际dry-run，三文件原始投影hash保持上文值。

## 实际测试覆盖清单

以下是完整相关新测试文件中的test_方法数量，不是unittest最终执行数：部分继承fixture会展开更多测试，subTest也不等于独立测试数。正文与辅助断言均在TESTS-DIFF可读；SDK替身、fake HTTP、临时CLI、Core分别标记，不能以文件名里有Hermes就称真实Host。

| 完整相关测试文件 | test_方法数 | 主要证据层 |
| --- | --- | --- |
| `tests/test_hermes_memory_complete_scan.py` | 3 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_flush.py` | 10 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_flush_append.py` | 4 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_flush_arguments.py` | 8 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_flush_cursor.py` | 9 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_flush_errors.py` | 5 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_install.py` | 5 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_install_arguments.py` | 6 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_install_cache.py` | 13 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_manage.py` | 12 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_provider.py` | 14 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_provider_config.py` | 20 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_retrieval.py` | 12 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_retrieval_quality.py` | 1 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_retrieval_unicode.py` | 5 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_summary.py` | 12 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_summary_quality.py` | 1 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_hermes_memory_turn_bytes.py` | 4 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_memory_owner_append_scan.py` | 14 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_memory_owner_scan.py` | 11 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_roleplay_recall.py` | 33 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_roleplay_recall_eval.py` | 13 | 本地临时/合成；部分SDK为替身，不能提升为Host |
| `tests/test_roleplay_recall_lifecycle.py` | 9 | 本地临时/合成；部分SDK为替身，不能提升为Host |

## C2差异文件逐字节绑定

raw SHA对应冻结时原始bytes；LF文本SHA用于审查patch重建。旁线文件不纳入L1，也不把它们的全量结果算给X2 HTTP。

| 文件 | raw SHA256 | LF文本 SHA256 |
| --- | --- | --- |
| `runtime/life_engine/character_onboarding.py`（旁线排除） | `d7aa18543a5ba1ac1f961bf41f104689854477294b871962f40b2a1420b525e0` | `32f86d7c9bb3df6580254c601cac364904c3a6e5edb417c3fe1709752840efd1` |
| `runtime/life_engine/domain.py` | `aabb98655fb9351fb9ad0e14fb0b015d2362b1e4379fea528b8dd5c5a2f7b606` | `6552804abb344c8236c7b078c011a4ec52505af3bae36860b7a8f5dfcdaebb8b` |
| `runtime/life_engine/hermes_card_hook.py`（旁线排除） | `5c086b937f50de1095011fc0a918ec0560c3ab86d76e0c1949de5b66093b6a02` | `aa2c587ff1d571a11771b6e45afa6b7f21a1857899ceb2d3ada367b598f6a2ce` |
| `runtime/life_engine/hermes_card_native_hook.py`（旁线排除） | `f612ed3433dac7d4f5a02ba9d9d412563086cf8d0684a172c236a1b647e9bc9e` | `9a8956116d1ac57f7dd96df9ffeef0395522045b5f9f8224cf61f4cd0701965a` |
| `runtime/life_engine/hermes_card_runtime.py`（旁线排除） | `5a23829ca01eda1c0cf37e1ac051574df8b196ea84affffcd6320e7aff204366` | `001034f1b96f5b525aad9c4f032430a481620185822028b44f9b23d532168792` |
| `runtime/life_engine/memory_repository.py` | `926478609f3da991cfd646f7d32ec81b00b5ff13211efca540e7e5e85b05174d` | `5b2bc17821c31d5c4b383c03996a4bb84a4bae6e45f03ee9b0bce59451049a2d` |
| `runtime/life_engine/memory_runtime.py` | `78ec9462d90b39f95dcdca9a7a253a63569c927f96a7e022bb07c671c6fb26dc` | `b6cea3e2584d8f1f7a702eb8ecedf0418aa8ba13e0b597bb1c47e0eaaff1730f` |
| `runtime/life_engine/prompt_runtime.py` | `6ab3f4b830f0761ad3e487bc03601171283c3790db7d3e58836c928aa76bb9aa` | `7253f6f80bd48c6acc4ba154d80ed808160700d5ee8fb8b337fde75c1c1f7d4d` |
| `runtime/life_engine/roleplay_recall.py` | `04052e70cc0c5ce5e288815acbe21fc72022bfb21845e8592b918b61139c2cf0` | `04052e70cc0c5ce5e288815acbe21fc72022bfb21845e8592b918b61139c2cf0` |
| `integrations/hermes_memory/__init__.py` | `2af24885dcb799df2ecbbafec294214476db266a3076807357c2feddc7d4d406` | `2af24885dcb799df2ecbbafec294214476db266a3076807357c2feddc7d4d406` |
| `integrations/hermes_memory/plugin.yaml` | `4dd8f40b11745958a64a7c7639b8a5d7c420d5f5a5f011840c4f8ac7d37de940` | `4dd8f40b11745958a64a7c7639b8a5d7c420d5f5a5f011840c4f8ac7d37de940` |
| `integrations/hermes_memory/recall_service.py` | `c2632dc4603d11094e1bcf832c08b71bee41337bed1d569271a3dc0af20c72b8` | `c2632dc4603d11094e1bcf832c08b71bee41337bed1d569271a3dc0af20c72b8` |
| `tools/hermes_memory_flush.py` | `629ae569f0dbf9805b1b912758ca67cc43c61fa479d901cda0cb0c4679c39e78` | `629ae569f0dbf9805b1b912758ca67cc43c61fa479d901cda0cb0c4679c39e78` |
| `tools/hermes_memory_install.py` | `444cbd29cd3acc499b136f1624d50cdd7b43aa1f7a5d7bb20589b3191f852efb` | `444cbd29cd3acc499b136f1624d50cdd7b43aa1f7a5d7bb20589b3191f852efb` |
| `tools/hermes_memory_manage.py` | `563bf65f308072b3cae245e5707a249544be34fa23be2d6bd6cf83969a8d2e79` | `563bf65f308072b3cae245e5707a249544be34fa23be2d6bd6cf83969a8d2e79` |
| `tools/roleplay_recall_eval.py` | `c23c09e422e575b7c5306ec31a03541ee26fd71808b75ab88f1f5a5231ffc29d` | `c23c09e422e575b7c5306ec31a03541ee26fd71808b75ab88f1f5a5231ffc29d` |
| `tests/fixtures/roleplay_recall_eval/v1.json` | `82859adddc510cf350dcf963f8456cd43f1f135b8de9de2784faab2a959eebc0` | `82859adddc510cf350dcf963f8456cd43f1f135b8de9de2784faab2a959eebc0` |
| `tests/test_hermes_card_native.py`（旁线排除） | `e7cac3e43fe135c86874a4d796823015101cd5436e642589ec5a58d4ec16d477` | `21bfe8f0fc80869afe75ece6b31215a3bc1bf60c98d65519054d64e212ffbcf1` |
| `tests/test_hermes_memory_complete_scan.py` | `c6a3bf951806a0d22d29832ca421fd02885489754f558733750cb81b956a745d` | `c6a3bf951806a0d22d29832ca421fd02885489754f558733750cb81b956a745d` |
| `tests/test_hermes_memory_flush.py` | `2c2fb0d1a179acb56bf3a0448d1d5105e868a49084f396fc83b6e2fb4aafe5f8` | `2c2fb0d1a179acb56bf3a0448d1d5105e868a49084f396fc83b6e2fb4aafe5f8` |
| `tests/test_hermes_memory_flush_append.py` | `1e294f95cef48bb5940c8ab4a8236867fee9de936770dbf8406cd90ed061b303` | `1e294f95cef48bb5940c8ab4a8236867fee9de936770dbf8406cd90ed061b303` |
| `tests/test_hermes_memory_flush_arguments.py` | `8a550be8f4df2c7f37bc24d7bad89b78b0f107c0f5fda10da65b88902cf9655d` | `8a550be8f4df2c7f37bc24d7bad89b78b0f107c0f5fda10da65b88902cf9655d` |
| `tests/test_hermes_memory_flush_cursor.py` | `491f197f7afa1bc423b608baa62b5e7dd2c9177fba77af4a21bd7db2b37f1f3a` | `491f197f7afa1bc423b608baa62b5e7dd2c9177fba77af4a21bd7db2b37f1f3a` |
| `tests/test_hermes_memory_flush_errors.py` | `298cc7de798bf6dbd049508eb1e4acbddcdbe9457358ce593629ecf0fe2ee7c9` | `298cc7de798bf6dbd049508eb1e4acbddcdbe9457358ce593629ecf0fe2ee7c9` |
| `tests/test_hermes_memory_install.py` | `07274716608277d53c980cbaf9852453c751f110515e16ee96f4f47254369a1a` | `07274716608277d53c980cbaf9852453c751f110515e16ee96f4f47254369a1a` |
| `tests/test_hermes_memory_install_arguments.py` | `f3c8e4d429cf20d40dbe26d8b9e0e87bc3a9f87f391603c68b3e267e21296fbf` | `f3c8e4d429cf20d40dbe26d8b9e0e87bc3a9f87f391603c68b3e267e21296fbf` |
| `tests/test_hermes_memory_install_cache.py` | `4d9eb6f8c23de15b437ccd3c071d41d2893ef52d4d75a03dd0793031258eaa5c` | `4d9eb6f8c23de15b437ccd3c071d41d2893ef52d4d75a03dd0793031258eaa5c` |
| `tests/test_hermes_memory_manage.py` | `bad1ef094996cc9b6d64274b10f5127dc7c348f48ce2f8810d8d614cf5ef1197` | `bad1ef094996cc9b6d64274b10f5127dc7c348f48ce2f8810d8d614cf5ef1197` |
| `tests/test_hermes_memory_provider.py` | `c355e60ddfa4a07916660f680960be104f31e6a3bf1f85d2af3c80a2f330cbf5` | `c355e60ddfa4a07916660f680960be104f31e6a3bf1f85d2af3c80a2f330cbf5` |
| `tests/test_hermes_memory_provider_config.py` | `95e085b424c05998e20407edefd8b38436f75f4e3352e437e73cb89542d13cb7` | `95e085b424c05998e20407edefd8b38436f75f4e3352e437e73cb89542d13cb7` |
| `tests/test_hermes_memory_retrieval.py` | `932951b5465e6346b698ba22ca22646c6304208d4bd6bf031813acbfe0dbc543` | `932951b5465e6346b698ba22ca22646c6304208d4bd6bf031813acbfe0dbc543` |
| `tests/test_hermes_memory_retrieval_quality.py` | `a5aa7f19eb3fd5d4ca3f9a1a2247f12f97d5f4d54b0a69182031aa437dfe7476` | `a5aa7f19eb3fd5d4ca3f9a1a2247f12f97d5f4d54b0a69182031aa437dfe7476` |
| `tests/test_hermes_memory_retrieval_unicode.py` | `d11ae7cc21718e2ebb39444f83650534ecd27e4e99f97caab3f5f9338bf39715` | `d11ae7cc21718e2ebb39444f83650534ecd27e4e99f97caab3f5f9338bf39715` |
| `tests/test_hermes_memory_summary.py` | `5478e8aadf53df9e484ffc070b5c93724031bf78e6bb5f3679d170a2d00eb12f` | `5478e8aadf53df9e484ffc070b5c93724031bf78e6bb5f3679d170a2d00eb12f` |
| `tests/test_hermes_memory_summary_quality.py` | `ca2f6a23b314ed559720a740c094220c1f0a0d718a07a516bf190d8bae98d6dd` | `ca2f6a23b314ed559720a740c094220c1f0a0d718a07a516bf190d8bae98d6dd` |
| `tests/test_hermes_memory_turn_bytes.py` | `ac705a26f2f387d965b02eb7f1a9fd5696cc39d094689fde69e15d90861f90c6` | `ac705a26f2f387d965b02eb7f1a9fd5696cc39d094689fde69e15d90861f90c6` |
| `tests/test_memory_owner_append_scan.py` | `ebe437ead7589c057b581751bf82a864062feb8b29f206942d86502fc8b456c8` | `ebe437ead7589c057b581751bf82a864062feb8b29f206942d86502fc8b456c8` |
| `tests/test_memory_owner_scan.py` | `d975fa0f22c58cba3a2605117b5a34d8aa5e06babf3eed373e80748f3c9c565d` | `d975fa0f22c58cba3a2605117b5a34d8aa5e06babf3eed373e80748f3c9c565d` |
| `tests/test_roleplay_recall.py` | `f782184dcd470b65a1216938d9d5ae9fd84736749d305cc84312158dae7fe0f8` | `f782184dcd470b65a1216938d9d5ae9fd84736749d305cc84312158dae7fe0f8` |
| `tests/test_roleplay_recall_eval.py` | `2613d90ad68e3df895667ab000c1d653c91c2be42dee94b6d966c6da62add3f1` | `2613d90ad68e3df895667ab000c1d653c91c2be42dee94b6d966c6da62add3f1` |
| `tests/test_roleplay_recall_lifecycle.py` | `80699989df095b62222e6d2955d8da69b024d23f5a2f7dd6800dbc601778ea56` | `80699989df095b62222e6d2955d8da69b024d23f5a2f7dd6800dbc601778ea56` |
| `tests/test_user_identity.py`（旁线排除） | `55dd134cad4fa2a5cc6700eb8f1625bb3b0c8c7fb83a681f35920db7f39111a4` | `55dd134cad4fa2a5cc6700eb8f1625bb3b0c8c7fb83a681f35920db7f39111a4` |
| `examples/cosplay_recall_trial.py` | `c3f497fa16977ae008c24b7d51eabb1e9c91575e09ce0a75a058d8353ac297d4` | `c3f497fa16977ae008c24b7d51eabb1e9c91575e09ce0a75a058d8353ac297d4` |

## 证据原件hash

| 原件 | SHA256 |
| --- | --- |
| `manifest.json` | `045ed49ac08ead503df47133ae669810766abcce2ce666bb5ed693ac669abc02` |
| `reuse-probes.json` | `fddca36674933a5f5a1f0583f1325a1110a40bfbc1362ab84edf6e24c1b475f1` |
| `core-path-proof.json` | `52e68fa4e079c23c6924aaeab9a771b47bb627b3c2674b4b19922a27a638883b` |
| `core-projection.json` | `231fb2c66320540126c469fb4d53373a6a0b099ada5e7a3df67478c517c77794` |
| `c2-evaluation.json` | `d77bb91aeb8bde57b639430a584ff5d768c24425111d1474bd090ee0387bf3b1` |
| `le64-candidate-full.log` | `2bb6d64dac050ca0cc42d51e228f1dcc3d21aa861ac0360f8c22209fe2bea83f` |
| `initializer-proof.json` | `93ab2885b1b9983c5e6806817f8acb7a376bf8b9ef25a258e2260edf31381b2e` |
| `review-static.json` | `04794361dbdec75ec9aa52a5788e51938362264a4c19e3d7b099e9377f9b07d4` |
| `le64-core-projection-tests.log` | `38c0df650c0a517fa7b9790d3ca42d1da360feb56380d987dd0768acc6e3da17` |

### C2完整187文件清单

<details>
<summary>source manifest（raw hash）</summary>

| 路径 | SHA256 | 与Base语义不同 |
| --- | --- | --- |
| `runtime/life_engine/__init__.py` | `56b5e91c3bb77ab933c25fd65eba883419bdc5691cc94cb9dc840e8f4e3674eb` | NO |
| `runtime/life_engine/bridge.py` | `46fc99f022c7c2e2422fca9ee47046019aa41a2ec16800253d66cdea8cfd23f9` | NO |
| `runtime/life_engine/bridge_codec.py` | `95b34e5a4b6201677ea4716ba3f4e6928fa6219d3f228eab7c58eec66fa4ce55` | NO |
| `runtime/life_engine/bridge_control.py` | `233c8fe22645163e715a71b3cd4b6271c516cc3b5d55670b5d54c87cf54c9565` | NO |
| `runtime/life_engine/bridge_repository.py` | `79e21fc6a9cd5fc58207391cd828597fba6de2e4a839eea461cd0e27864e5287` | NO |
| `runtime/life_engine/bridge_runtime.py` | `20c683e1e160e0d512af14a843499dd6288f97017c9717a928e5f094c46e33b3` | NO |
| `runtime/life_engine/bridge_schema.py` | `4487591493890be48eef04608dd405b5b68040990fa0aace445c656b526f5d76` | NO |
| `runtime/life_engine/bridge_sqlite_repository.py` | `40241ac4ba703eee7542f5d41ca5f7e4f73edad36237f09d6afa9870f9e848f8` | NO |
| `runtime/life_engine/bridges.py` | `f718654cc92cc37fd1f1374c0408aa0c7883532f5af82787da99d800e3b05d65` | NO |
| `runtime/life_engine/character_continuity.py` | `e26046df5bbec2617973c9e045ff1cdade2f24b5c31a5b3ca3f0c4b25e943515` | NO |
| `runtime/life_engine/character_onboarding.py` | `d7aa18543a5ba1ac1f961bf41f104689854477294b871962f40b2a1420b525e0` | YES |
| `runtime/life_engine/cli.py` | `6b2b0aa74cc828d1f66540a911ee65962dcee7eff9f0a6d65dbfbb9aebf783bb` | NO |
| `runtime/life_engine/compat_scan.py` | `f1c8974aa109ad0c2b54d35f43acbdcf5a0d6d5fe97a99f2dd157e484cd07697` | NO |
| `runtime/life_engine/config.py` | `0ccb31f7d836576864e5d56e1864f5e37369f8d1e00fb03b428daf814f7f889a` | NO |
| `runtime/life_engine/deploy_cli.py` | `02ed332c825ed501626412d04cf09ae463b2818df4be63f4400e56eb5418372d` | NO |
| `runtime/life_engine/domain.py` | `aabb98655fb9351fb9ad0e14fb0b015d2362b1e4379fea528b8dd5c5a2f7b606` | YES |
| `runtime/life_engine/domain_lifecycle.py` | `7df6ccc673610613b3f9e7a83a8de2836e80369c405001df16334721a8e3e0d3` | NO |
| `runtime/life_engine/domain_policy.py` | `962850a3ea8272aad863d2c6987973bdd052bc8535a2ad29971689570a278c73` | NO |
| `runtime/life_engine/durable.py` | `8b140cf14543640c7e290b398bcd9b6a8793967edbe81ff2c6ff3cf3f21f7189` | NO |
| `runtime/life_engine/engine.py` | `99580cc4b5bb6d0ddab3f5b4069af367d99df146b68b7520941a9e6ea121e3f3` | NO |
| `runtime/life_engine/hermes_capabilities.py` | `34bcad67e0d039269fcdd581a85809858ecb9a157c401c6adc8aa1cb8c14ec34` | NO |
| `runtime/life_engine/hermes_card_hook.py` | `5c086b937f50de1095011fc0a918ec0560c3ab86d76e0c1949de5b66093b6a02` | YES |
| `runtime/life_engine/hermes_card_import.py` | `0be012ce03676ddf84dd7cfa358059479f220f21e0e30a064ddd5c33aa4c8086` | NO |
| `runtime/life_engine/hermes_card_native_hook.py` | `f612ed3433dac7d4f5a02ba9d9d412563086cf8d0684a172c236a1b647e9bc9e` | YES |
| `runtime/life_engine/hermes_card_runtime.py` | `5a23829ca01eda1c0cf37e1ac051574df8b196ea84affffcd6320e7aff204366` | YES |
| `runtime/life_engine/hermes_profile_setup.py` | `f4117a322bf4ad0896debce15b530d0b0eaf288b97e15bed975b69ae0659de6f` | NO |
| `runtime/life_engine/hermes_turn_proof.py` | `1ff9da64e16a2245ed1ba86366332532fb06c9a036306226123824f00feef47a` | NO |
| `runtime/life_engine/import_cards.py` | `c14f49dc6111b420473394f19bcb81d22533cef04f3497c6510a634de1f1f324` | NO |
| `runtime/life_engine/import_ir.py` | `56ccaaa93efc322f6056e87caab20d60fd815e3508a0a536ad1df6cb5e30b930` | NO |
| `runtime/life_engine/install.py` | `2733f888aafebd46b34f90d58b1727c4e9600f61e6cef692d4fad432bb35975a` | NO |
| `runtime/life_engine/integration.py` | `1733b63b8ab1da554b19ac161e5f0689f88fafbc451bf7418b31dc6b7938bafc` | NO |
| `runtime/life_engine/living_domain.py` | `8140a1ec4f3d4b0d0ed0a1daa1404b4b3a72d5fa0e5e905c2f7e6840cbb26c35` | NO |
| `runtime/life_engine/living_host_binding.py` | `2a0aededdef4fe31bbb44e529da86e6d173a2f1a282700778cf29f27fc8ded99` | NO |
| `runtime/life_engine/living_host_capability.py` | `b5681e7b003634805a2a62230a595085cc4de465f88d1fc3d7e0caa7d0c7db86` | NO |
| `runtime/life_engine/living_host_evidence.py` | `c16535f27d6af3e47766b91c4c8e8c982327a256831b50c7f78020af27f28d2d` | NO |
| `runtime/life_engine/living_host_facade.py` | `7acd9e2ac894081cb1946a79693bf2ba75f4417201389215df7013324e7d26bd` | NO |
| `runtime/life_engine/living_host_metadata.py` | `60a6ec4e759a1e4ff0c00490734a496e1dbb751173dc6c1c827d641ba34c3a38` | NO |
| `runtime/life_engine/living_migration.py` | `825c6e4bbaa0ca3c62f0da55db205b88dd064fb40381fe97a2d4204ee690f6ed` | NO |
| `runtime/life_engine/living_policy.py` | `526dba3404e8310e98e25966cbe3fe40588a6bfe2c91e566ddf68a441012f049` | NO |
| `runtime/life_engine/living_projection.py` | `64f8154ab49ec9bfb5be459a732a769c465426221e0b17172617649583802996` | NO |
| `runtime/life_engine/living_real_delivery.py` | `af3dcc9716f383b301d85787e93fdcbdf5dbde4f786f43512ae767ef40d05866` | NO |
| `runtime/life_engine/living_recovery.py` | `bc9b906b6f37674551e62d38d239a4bad1b7cfd4d655cfc6d0078b605879aa43` | NO |
| `runtime/life_engine/living_repository.py` | `1f429a67cecbe5e1108f3c2c55c011d5d08f3bf573e26b2f6939e51fecd97e0a` | NO |
| `runtime/life_engine/living_runtime.py` | `de233a9647d00f366d0d89e407d933caac4f762bc724a4ab89bb7063e0efa265` | NO |
| `runtime/life_engine/living_schema.py` | `85f5b6d6b86892f2404ab10814087d9addbdbbd4a249872ab6e07b01b20bd1d9` | NO |
| `runtime/life_engine/lore.py` | `00c4928da401117949fc0396c6f9fcaeb5dc750916c6c4887504a3c37aa8e7da` | NO |
| `runtime/life_engine/lore_normalize.py` | `90a67b927a80c81ab60a2ac02b5ee9e262dbd792396e8ca804b3596100a96229` | NO |
| `runtime/life_engine/lore_repository.py` | `50d3370b769000f358f527cbef1759b032f9d6c3fed61cee487c4ae807c29934` | NO |
| `runtime/life_engine/lore_runtime.py` | `1b12ef162ca4bd577a39119e140fd5415547afcaf85b9eb4e40662cb6b7f8350` | NO |
| `runtime/life_engine/lore_schema.py` | `96ecd24b3640b38932f09c2a6c0a413dd8ecba262163d44a3edaa2727e9d4c60` | NO |
| `runtime/life_engine/lore_sqlite_repository.py` | `5bf1938123510148ae18316db3271706f142cc04a7b9e102fb3a7455b304fc27` | NO |
| `runtime/life_engine/memory.py` | `9df9482a0a30d4b79a59e4cd67522f2374261d1d6d86203b13ebb827e053418e` | NO |
| `runtime/life_engine/memory_control.py` | `24bd48305f918a9fb35ac957b6a59db973875bc488683a2220a84fe819799268` | NO |
| `runtime/life_engine/memory_repository.py` | `926478609f3da991cfd646f7d32ec81b00b5ff13211efca540e7e5e85b05174d` | YES |
| `runtime/life_engine/memory_runtime.py` | `78ec9462d90b39f95dcdca9a7a253a63569c927f96a7e022bb07c671c6fb26dc` | YES |
| `runtime/life_engine/memory_schema.py` | `35b6cb1324b43e8ae675c28f0104a02b9226c7d1dd36af4a98f9e967ad9124e7` | NO |
| `runtime/life_engine/memory_sqlite_repository.py` | `a1c7db668aecc9f2d72f3bfc0054c8e7d109bad434c2d364c4f6e3fa7c1abff9` | NO |
| `runtime/life_engine/migrate.py` | `afbbc3031c8cf6f5c3b4e5468e928ceccedec3a6737c7f7bb8b3a052cc97a154` | NO |
| `runtime/life_engine/photos.py` | `0034e5cce83bfec6b15a7a3d25fd4ce2e09dd8d28aaf5ecacaa034bdeb4fea4b` | NO |
| `runtime/life_engine/prompt.py` | `47c8a37a6d37eaac631b0c0f5f0022ba4016f2185086a3ef15e4577f441b3726` | NO |
| `runtime/life_engine/prompt_codec.py` | `165eca7d476f484d3d72fdde5972196cc0b239b9d59e1704f38fa2ff5710cec5` | NO |
| `runtime/life_engine/prompt_runtime.py` | `6ab3f4b830f0761ad3e487bc03601171283c3790db7d3e58836c928aa76bb9aa` | YES |
| `runtime/life_engine/roleplay_recall.py` | `04052e70cc0c5ce5e288815acbe21fc72022bfb21845e8592b918b61139c2cf0` | YES |
| `runtime/life_engine/sandbox.py` | `1f98db13d3e8038cf36ef078f2b8df26289c0794940d6eb1937adac2f1f92b3e` | NO |
| `runtime/life_engine/setup.py` | `3c3bf063db78432e5f69e1e06d63d2196fb572502693466053026407341f7bac` | NO |
| `runtime/life_engine/store.py` | `18879b0ae3ba768d6f295ed713f8f8396439b22ec260f5a04058b9633dee248b` | NO |
| `runtime/life_engine/story.py` | `b0b73484f5ae4bc5fd2e547fd48102d6ba253a30f16c49e9acae020183030f40` | NO |
| `runtime/life_engine/story_codec.py` | `64cacb104b46de589bc5ef100357095220a9525f5b0068f8fb7341f1a5869c57` | NO |
| `runtime/life_engine/story_reducer.py` | `6e6a8aedab37977ee74c50a6f776455c7ed00d87eea49450136b206bcddb8864` | NO |
| `runtime/life_engine/story_repository.py` | `cf73a0228462b01dcb4d6fd7b9835f794fe7fc1d1d1e7fbe31d878e533ccc28f` | NO |
| `runtime/life_engine/story_runtime.py` | `ea2ff89112b44f574911bd48b3e4598cd12d4882feb2aee3d03cf51a08927117` | NO |
| `runtime/life_engine/story_schema.py` | `62af2e596242862455757e8c5c5455e03ccb292864c496437570bd623578836c` | NO |
| `runtime/life_engine/story_sqlite_repository.py` | `6b619907f2dc302030f65b0e1409242601dc0f3b6008db4efe5141cdcf71f1eb` | NO |
| `runtime/life_engine/world_codec.py` | `479eaf155a11eb1b0c59dcc79fbba213f8cb0f0b6f6700f66a98b23d73fad085` | NO |
| `runtime/life_engine/world_repository.py` | `abc5f7d65490de06a154dd0e96454cb5a1c89821419b51ae5bfce89004beea20` | NO |
| `runtime/life_engine/world_runtime.py` | `b0af177ba62cb452552d1b2416ab4d55acc2c44e82d3a3d27ec00728adbc2da6` | NO |
| `runtime/life_engine/world_schema.py` | `e97ebd29405de0b25622f08a74274d2420d4c2b7ad79f7149b85631ca88bf2a0` | NO |
| `runtime/life_engine/world_sqlite_repository.py` | `a1165fb302ec9a92603a0ca353188d1ff971fbd49d1d7275670e7ec92ba656e5` | NO |
| `integrations/hermes_living/__init__.py` | `255c781c54eef324f607301b81959030894b5faec8f7e00c1bf3cdcb78213288` | NO |
| `integrations/hermes_living/adapter.py` | `7eeaefac9c1ed946783b47796711d3d511d4a4a6a556b80a00c78dfd03096ea2` | NO |
| `integrations/hermes_living/plugin.yaml` | `e9e5e3ee37691e7661738110d96e8a91494dd521e0cca5d403fa01726db63ac2` | NO |
| `integrations/hermes_living/provider_ownership.py` | `73329666d156c94018a043e322713840d0fe85815a891ad33b40075cd84a4bea` | NO |
| `integrations/hermes_living/provider_transport.py` | `bdaad90dd3aece7f1b4dbbdaa400a8609daa2b18c66203097dac7f196cf9b7e1` | NO |
| `integrations/hermes_memory/__init__.py` | `2af24885dcb799df2ecbbafec294214476db266a3076807357c2feddc7d4d406` | YES |
| `integrations/hermes_memory/plugin.yaml` | `4dd8f40b11745958a64a7c7639b8a5d7c420d5f5a5f011840c4f8ac7d37de940` | YES |
| `integrations/hermes_memory/recall_service.py` | `c2632dc4603d11094e1bcf832c08b71bee41337bed1d569271a3dc0af20c72b8` | YES |
| `tools/hermes_capabilities.py` | `67345e44b3f440c39aa045eca964a83e1c777d19e220e321aebd4a303f52f56c` | NO |
| `tools/hermes_card.py` | `be4bf257f77908e7035294c54f27e2a97adf6e5ebe4e9baba81a5012e13bba49` | NO |
| `tools/hermes_character.py` | `4210199640f486319fd97807ba7ff9dbe55e57d0595f6d3fdfbc2be84fe87028` | NO |
| `tools/hermes_continuity.py` | `80841cc28223c1b5531bf87e1d4e296ef2bc0f2bd702d87a7159f213add91760` | NO |
| `tools/hermes_memory_flush.py` | `629ae569f0dbf9805b1b912758ca67cc43c61fa479d901cda0cb0c4679c39e78` | YES |
| `tools/hermes_memory_install.py` | `444cbd29cd3acc499b136f1624d50cdd7b43aa1f7a5d7bb20589b3191f852efb` | YES |
| `tools/hermes_memory_manage.py` | `563bf65f308072b3cae245e5707a249544be34fa23be2d6bd6cf83969a8d2e79` | YES |
| `tools/hermes_native_host_probe.py` | `064597c4a9c336abd8e259329bb338e825a8ee0f3394e67c0acdfc1ce773308f` | NO |
| `tools/hermes_text_baseline_probe.py` | `09dc43e0303c32c69919278c3219256aa7dc37ca915ae3a8aa7b6c363c6cd347` | NO |
| `tools/roleplay_recall_eval.py` | `c23c09e422e575b7c5306ec31a03541ee26fd71808b75ab88f1f5a5231ffc29d` | YES |
| `tests/fixtures/roleplay_recall_eval/v1.json` | `82859adddc510cf350dcf963f8456cd43f1f135b8de9de2784faab2a959eebc0` | YES |
| `tests/hlv3_crash_worker.py` | `190c2e0cd2f51c0f79a04f65002dc83cabe5cca210971ed8daa850c8a61e4ca3` | NO |
| `tests/hlv3_lifecycle_worker.py` | `0c929c0275a378e0ec742262dd530a0f5636870c18273858ccc0cd5536d41a4b` | NO |
| `tests/hlv3_validation_support.py` | `2a416181a4f963491339cbfa84fa698600de86c7c00a8aebb4264873ddf7ab07` | NO |
| `tests/hlv4_a1_crash_worker.py` | `bd3de1f9e6c22397443f809817e6760206d27e29d9a187501190d58d0d55b82f` | NO |
| `tests/hlv4_r1_crash_worker.py` | `8efc62bf06f5c0e6fa3584a6b88750621b920e092783b908714b0d81d5d049a9` | NO |
| `tests/living_host_process_fixture.py` | `6d54a53fff0be0b9a9d6f36a98616dc2d8383a7ae188aa7d2b1ea5af8d34edbb` | NO |
| `tests/living_process_fixture.py` | `8babc804001078a23b7b101af141d176b94597d29cd5388b6acd028539867f66` | NO |
| `tests/living_recovery_process_fixture.py` | `623068cb8fca7d86bab5ee945fa7d3a4723fbaa44c9876208276c593cd5192fb` | NO |
| `tests/living_time_fixture.py` | `de73df6e5f50f8b03f758eb57fa600f1c2a9bad54769916c62754ca8e2f52591` | NO |
| `tests/m1a_probe/__init__.py` | `979c9c59e0d4d4f1a201cd6ac7ad9a78525eb57b067111e5598bd016e8acfc23` | NO |
| `tests/m1a_probe/collect_evidence.py` | `3b375d4240dc6b412eef896f2e3be14a648f9db6d878f677f1621a2a1431a6cd` | NO |
| `tests/m1a_probe/fault_worker.py` | `d884672f966b9be50870c99e88903fa4ee5bb332c57f3286830a89579745b777` | NO |
| `tests/m1a_probe/gate_worker.py` | `564b6e78a9679454b24c6153406519b349cd3ff370aec71c11ac8c6cf44b0c11` | NO |
| `tests/m1a_probe/isolation.py` | `38974d298cb2d74bd794bc92299cddf8763ebdec1a5baebd578c912a0fdb6d86` | NO |
| `tests/m1a_probe/pack_evidence.py` | `f5b3a55a8182d20f9768c81dbddfa4fe6ee615906e6468395123a3dbada92198` | NO |
| `tests/m1a_probe/primitive.py` | `a3bdedb1b03324ca5b121bcb2837504d45af1cc665630d01487f8cc8b7b16633` | NO |
| `tests/m1a_probe/query_worker.py` | `05439ef375591ed72a1cdbad54c0e164c186737578680b631d884e658af226bc` | NO |
| `tests/memory_fixture.py` | `bc0d5e2c986f8e55f8838ff2a87db8bdcd17ac5b45a76036908b2bf57032a91a` | NO |
| `tests/test_bridge_runtime.py` | `14de7b811dfb90ca91e6cf2cb0ca99ab3a96a2135ae20ee00a7ebfcbd0d59123` | NO |
| `tests/test_character_capabilities.py` | `ce75c5dd962a46dd9c6ac0fc0d323fb4a86ffeeed180d594491f9d79731feab9` | NO |
| `tests/test_character_continuity.py` | `1b780351aa356b37a50f8f5525f6635cc3619fa8806fb15f69b421fb41a75413` | NO |
| `tests/test_character_onboarding.py` | `a4fdd512503fdb11f60d7bfd1d11e95244fab995f09a1a1ceac558e02fd93152` | NO |
| `tests/test_domain.py` | `fe6fa307ae3dbdef2a9ea4bb14b52bd5487d66d959ff337e783d321d5c48d3c4` | NO |
| `tests/test_durable.py` | `68f5d1e64c24cb6745a7e6cc3ae7ed87fd7903872bbd840b65261b4ce8f9926f` | NO |
| `tests/test_engine.py` | `3b2f928ff950ae3573e9e60cc58aed190740bdf522e9e4d18c3b6fbc8a1d59fe` | NO |
| `tests/test_experience_x1.py` | `e7aa4b6157cfed71d75e046ba5095c19fe4532953d0d20e672867a585efaa534` | NO |
| `tests/test_hermes_card_import.py` | `848fe5568fdd72c7438501efca152e8c5a7644c9df6dacfa6c2251ce4f8e43ef` | NO |
| `tests/test_hermes_card_native.py` | `e7cac3e43fe135c86874a4d796823015101cd5436e642589ec5a58d4ec16d477` | YES |
| `tests/test_hermes_memory_complete_scan.py` | `c6a3bf951806a0d22d29832ca421fd02885489754f558733750cb81b956a745d` | YES |
| `tests/test_hermes_memory_flush.py` | `2c2fb0d1a179acb56bf3a0448d1d5105e868a49084f396fc83b6e2fb4aafe5f8` | YES |
| `tests/test_hermes_memory_flush_append.py` | `1e294f95cef48bb5940c8ab4a8236867fee9de936770dbf8406cd90ed061b303` | YES |
| `tests/test_hermes_memory_flush_arguments.py` | `8a550be8f4df2c7f37bc24d7bad89b78b0f107c0f5fda10da65b88902cf9655d` | YES |
| `tests/test_hermes_memory_flush_cursor.py` | `491f197f7afa1bc423b608baa62b5e7dd2c9177fba77af4a21bd7db2b37f1f3a` | YES |
| `tests/test_hermes_memory_flush_errors.py` | `298cc7de798bf6dbd049508eb1e4acbddcdbe9457358ce593629ecf0fe2ee7c9` | YES |
| `tests/test_hermes_memory_install.py` | `07274716608277d53c980cbaf9852453c751f110515e16ee96f4f47254369a1a` | YES |
| `tests/test_hermes_memory_install_arguments.py` | `f3c8e4d429cf20d40dbe26d8b9e0e87bc3a9f87f391603c68b3e267e21296fbf` | YES |
| `tests/test_hermes_memory_install_cache.py` | `4d9eb6f8c23de15b437ccd3c071d41d2893ef52d4d75a03dd0793031258eaa5c` | YES |
| `tests/test_hermes_memory_manage.py` | `bad1ef094996cc9b6d64274b10f5127dc7c348f48ce2f8810d8d614cf5ef1197` | YES |
| `tests/test_hermes_memory_provider.py` | `c355e60ddfa4a07916660f680960be104f31e6a3bf1f85d2af3c80a2f330cbf5` | YES |
| `tests/test_hermes_memory_provider_config.py` | `95e085b424c05998e20407edefd8b38436f75f4e3352e437e73cb89542d13cb7` | YES |
| `tests/test_hermes_memory_retrieval.py` | `932951b5465e6346b698ba22ca22646c6304208d4bd6bf031813acbfe0dbc543` | YES |
| `tests/test_hermes_memory_retrieval_quality.py` | `a5aa7f19eb3fd5d4ca3f9a1a2247f12f97d5f4d54b0a69182031aa437dfe7476` | YES |
| `tests/test_hermes_memory_retrieval_unicode.py` | `d11ae7cc21718e2ebb39444f83650534ecd27e4e99f97caab3f5f9338bf39715` | YES |
| `tests/test_hermes_memory_summary.py` | `5478e8aadf53df9e484ffc070b5c93724031bf78e6bb5f3679d170a2d00eb12f` | YES |
| `tests/test_hermes_memory_summary_quality.py` | `ca2f6a23b314ed559720a740c094220c1f0a0d718a07a516bf190d8bae98d6dd` | YES |
| `tests/test_hermes_memory_turn_bytes.py` | `ac705a26f2f387d965b02eb7f1a9fd5696cc39d094689fde69e15d90861f90c6` | YES |
| `tests/test_hermes_profile_setup.py` | `bdd1d06082b85b022dfb22c04cfc30f72ad77ce2d0211a5a6edb3b70e5cd48c1` | NO |
| `tests/test_hlv3_validation.py` | `208d8f4e4df328099d5ebb5924a348a0954748bd57c41dd011f4631e87b43f50` | NO |
| `tests/test_hlv4_a1_adapter.py` | `5d9600369a0c8dfef2e25910da4a3590da5ae30aa7c298c4997693bb9e88a846` | NO |
| `tests/test_hlv4_a1_r1_linearization.py` | `7127b679659401bc5c606d25960b08a27c7944b08755a0fb43b3ef93c313c0b0` | NO |
| `tests/test_hlv4_a2_r1_provider.py` | `dcd1c7fc3847c88416895548df62c36bddbc1c042bea807d7bcd17d7f69c7e7b` | NO |
| `tests/test_hlv4_r1_authority.py` | `fdf854ce1e31157c58c7b10f04335b7e25e2fa388c0e52e5141c6cb067dc97cf` | NO |
| `tests/test_import_cards.py` | `9e65a5d9197344ba5d786696716e6d3af67d692469faaff20133c2929dee613b` | NO |
| `tests/test_install.py` | `33c2fddd08dccfd29478fd894c0c1a6685f6a9ed2a26219c9a40da1f03400ba5` | NO |
| `tests/test_living_host_binding.py` | `706b070158fa640f012050795019d2815fcc97c1d1ac28a145ed566237ad3689` | NO |
| `tests/test_living_recovery.py` | `d4651c0d423e346c69be2e8ff9d6ce1d9ed9a117c90970324daeb2939391e2ad` | NO |
| `tests/test_living_runtime.py` | `0143336a32b5b48f25309254e375a42bb705c5cc4afba0596bb5d8d0f29b0bca` | NO |
| `tests/test_lore_domain.py` | `ccfa3cfeaaa52d8a5cfb57874ee7180e00e45f0d2b24c050c2a28d9432478ce3` | NO |
| `tests/test_lore_runtime.py` | `a4f4808340681bbe0b89c0af04f6ba0d778b3dc1d528c10c0bf5d5277fee37c2` | NO |
| `tests/test_m1a_probe_primitives.py` | `f7f9600b9dc0d3dbfdef5caa340e0bac6704b2e3e64d80f902579aad44119b1d` | NO |
| `tests/test_memory_domain.py` | `b3a6c20bbdd7ea53926970f33470d23bd50893c16db50a2ce8df213aaa25f795` | NO |
| `tests/test_memory_owner_append_scan.py` | `ebe437ead7589c057b581751bf82a864062feb8b29f206942d86502fc8b456c8` | YES |
| `tests/test_memory_owner_scan.py` | `d975fa0f22c58cba3a2605117b5a34d8aa5e06babf3eed373e80748f3c9c565d` | YES |
| `tests/test_memory_restore.py` | `57fb4f74068e4d99b4d76d09397d7b68d4fdb2553cce1af2427c81a011b15b3d` | NO |
| `tests/test_memory_runtime.py` | `e993076ec922d60212ba921188b1892e907b0086a9a33636fc5c922a44f6cfc8` | NO |
| `tests/test_memory_sqlite_repository.py` | `33a1a37856e5254b371906ff0238fe71ca5a6a7d91f0c38218ad0b80ad858f67` | NO |
| `tests/test_photos_migration.py` | `eec5b97ae8fb7f899a7cbd9e15b2dbc84805d2a59c9c96085d0e8c8390938b2d` | NO |
| `tests/test_prompt_runtime.py` | `dbcba123dc1582fcde221d674c37831f40df21e326ae5534cd235632c55f6bc7` | NO |
| `tests/test_roleplay_recall.py` | `f782184dcd470b65a1216938d9d5ae9fd84736749d305cc84312158dae7fe0f8` | YES |
| `tests/test_roleplay_recall_eval.py` | `2613d90ad68e3df895667ab000c1d653c91c2be42dee94b6d966c6da62add3f1` | YES |
| `tests/test_roleplay_recall_lifecycle.py` | `80699989df095b62222e6d2955d8da69b024d23f5a2f7dd6800dbc601778ea56` | YES |
| `tests/test_sandbox.py` | `f6bc2505547d65ea1ba942e735e4be45220dacca08b8245327d9f06f6fdf2e1d` | NO |
| `tests/test_schema3_migration.py` | `3c2c609815e6ef11cfc8136903a8e913b21977705a5c6ae8ce8b43eb516a209a` | NO |
| `tests/test_schema4_migration.py` | `3e489e05dd31a7c1307dcbed09113dcbf1554bb4132367c40d77a5a5e297f00b` | NO |
| `tests/test_schema5_migration.py` | `c7f2a26743c7896d81b5de7f51954a517cd323307432610e9581795047be37cf` | NO |
| `tests/test_schema6_migration.py` | `f19f70866a048ed43ab189a8bcd92aa7b4a27325271500ac6d804466e3b01e30` | NO |
| `tests/test_schema7_migration.py` | `128301de3b697dd47a264340f7ba16abb380cc59e5f22c2f8cae3c075bd294a8` | NO |
| `tests/test_schema8_migration.py` | `c7d1a372adaed02ca3e4aa674025f51638123d0e6f2c62dcb1a79a11ceaf70c9` | NO |
| `tests/test_story_domain.py` | `63c4b24e3716037459d10f94d80f419dd5fb15ca05fc1fe1e97d00d2079a5f63` | NO |
| `tests/test_story_runtime.py` | `1507963dba600105763f5df0021073a2aecedf3b3448c2022018c2ef457dac0c` | NO |
| `tests/test_user_identity.py` | `55dd134cad4fa2a5cc6700eb8f1625bb3b0c8c7fb83a681f35920db7f39111a4` | YES |
| `tests/test_w1_text_baseline.py` | `a5f7d729193a252e8725d98fd7d2e099e3a616ece72716b1ff76dada86a5dabc` | NO |
| `tests/test_world_runtime.py` | `3e27b3813081f3bbddab80c6315e3c0f3f579fc579f1dd7b1d3b162b7fd8dfec` | NO |
| `tests/test_world_sqlite_repository.py` | `35d44117dd29b84489519aa5eff64a764b7f8e5645c5051312995eba7ffd6d98` | NO |
| `examples/companion.answers.json` | `b299deb25ac469765be6d73c7e1dfdb7c1af4e695f6246fef9cb5732e1dab4d8` | NO |
| `examples/cosplay_recall_trial.py` | `c3f497fa16977ae008c24b7d51eabb1e9c91575e09ce0a75a058d8353ac297d4` | YES |
| `examples/experience_x1.py` | `cfa992c089f5bd6309e30f574e0238e2297df3c1d1cc66f941e0d7dc2f1774e3` | NO |
| `examples/graph-shape.example.json` | `aa19338b90ed7d4656f7b325f573a251b5075d2e98701d9932e9eb8d22285360` | NO |
| `examples/openclaw.answers.json` | `8599214346a323194e95043349b5bb814aa429c2150de44c8b80f29e2cc6bcfe` | NO |
| `examples/work-assistant.answers.json` | `61c0d2808f65063a5e866ef332b95bbcca403be3e9b31e29f8165a9a7ed9ba90` | NO |

</details>

本轮是作者持固定对象进行的候选复核，不签发第三方独立APPROVE。用户批准L1后，对真实实现的独立固定Head审核仍是交付门；模型/Host/生产/Schema/merge权限不由这些证据产生。
