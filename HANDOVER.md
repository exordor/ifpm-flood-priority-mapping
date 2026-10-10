# IFPM 移交说明

日期：2026-10-08。本文写给接手这个工作区的人，读完应该知道项目在做什么、东西在哪、怎么跑、下一步该做什么。给 Supervisor 的英文说明草稿在 `context/docs/mentor-explanation/Supervisor_Handover_Draft_2026-10-08.md`。

## 1. 项目是什么

IFPM 是一个洪水优先级（flood prioritisation）多准则原型。它把五大 PIM 准则（洪水 FH、泥沙/土壤侵蚀 SE、土地利用 LU、环境 ES、社会经济 SV）标准化到 0–1，按权重叠加成综合优先级图。结果都是原型或诊断级别（`diagnostic_only` / `provisional`），不是经过验证的洪水预测模型。

当前权重（Supervisor 完整规格）：FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14。每次运行实际使用的权重以输出目录里的 `run_manifest.json` 为准。采矿不再是准则，只作为单独的对比图层。

## 2. 研究区和现状

| 研究区 | 状态 | 主要输出 |
|---|---|---|
| 德国 Goslar（Abzucht 和 8 个法定洪水区的多河流扩展，约 739 km²） | 9 月最新工作，活跃 | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/`，`outputs/goslar_abzucht_display_rectangle_v1/` |
| 秘鲁 Secocha（A7367 Map 7 的 30 km² 参考窗口，不是流域） | 活跃，provisional | `outputs/peru_secocha_a7367_reference_extent_v1/`，`outputs/secocha_2023_validation/` |
| 旧秘鲁区 `peru_hybas_l7_6070641200` | 冻结基线，只读，禁止写入新结果 | `outputs/srtm_1arcsec_peru_pilot/`（含 7 个权重版本） |
| 津巴布韦 Upper Mzingwane（`boundary_v1`） | 背景案例，不再推进 | `outputs/boundary_v1/` 等 |

最重要的未解决问题：在 Goslar 扩展对比里，洪水准则在 8 个法定洪水区内都高于各自外围 1 km 环带，但综合优先级只在 3 个区更高。也就是说综合指数和洪水证据的关系还没理顺。

## 3. 目录地图

| 位置 | 内容 | 是否在 Git 里 |
|---|---|---|
| `README.md`、`AGENTS.md` | 工作区总说明；`AGENTS.md` 是一页纸的工作约定（目录、数据登记、建模规则） | 是 |
| `bin/` | 约 190 个处理脚本，按阶段分目录；入口和说明见 `bin/README.md` | 是 |
| `tests/` | 60 个测试文件 | 是 |
| `context/docs/research-map/` | 项目主记录：`EXPERIMENTS.md`（当前实验的命令、输出和结论）、`DECISION_LOG.md`（仍然有效的决定，含权重） | 是 |
| `context/docs/data-management/registry/` | 每个数据集的来源、许可和下载记录 | 是 |
| `context/docs/glossary.md`、`context/docs/methodology/` | 术语表；PIM 方法说明（中文） | 是 |
| `context/docs/mentor-explanation/` | 只剩给 Supervisor 的英文移交草稿和邮件草稿 | 是 |
| `data/raw/`、`data/validation/` | 原始数据，约 17 GB | 否 |
| `outputs/` | 所有结果，索引见 `outputs/README.md` | 否 |
| `exports/` | QGIS 便携包 | 否 |
| `ifpm-flood-pipeline/` | 独立的交付代码仓库（自己的 `.git`），只有合成数据测试 | 单独仓库 |

注意：`data/`、`outputs/`、`exports/` 都被 `.gitignore` 忽略。只 clone 仓库拿不到数据和结果，需要整体拷贝文件夹。

## 4. 怎么运行

环境（在工作区根目录）：

```sh
# 先装 uv（Mac 可用 brew install uv），再在工作区根目录运行：
uv sync --extra hydrology    # 按 uv.lock 装 Python 3.11+ 和全部依赖，生成 .venv
```

`--extra hydrology` 会装 WhiteboxTools，两条主链算水文时都要用；第一次运行时它会自动下载一个程序文件，需要联网。rasterio 和 geopandas 自带 GDAL，不用另外装。现有 `.venv` 是在 macOS 上建的，换机器需要重建。QGIS 只用来打开审阅项目，单独安装。

主要命令：

```sh
# Secocha
.venv/bin/python bin/factors/run_peru_secocha_chain.py
.venv/bin/python bin/validate/validate_peru_secocha_chain.py

# Goslar 扩展对比
.venv/bin/python bin/analysis/run_goslar_multiriver_full.py
.venv/bin/python bin/analysis/report_goslar_multiriver_full.py

# 测试
.venv/bin/python -m unittest discover -s tests
```

其余 Goslar/Abzucht 命令逐条写在 `context/docs/research-map/EXPERIMENTS.md` 对应实验下。

不要用 `python bin/pipeline.py run` 的默认链：它仍然指向冻结的旧秘鲁区。

快速看结果：用 QGIS 打开 `outputs/peru_secocha_qgis_project_package_compact/IFPM_Peru_Secocha_ReviewMap.qgz` 和 `outputs/goslar_qgis_project_package_compact/IFPM_Goslar_ReviewMap.qgz`。Goslar 最新结论的说明在 `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/READING_NOTE.md`。

## 5. Git 状态

- 以分支 `codex/goslar-validation-2024` 为准。2026-10-08 已把 9 月所有未提交的工作提交到这个分支（本地，未推送）。
- `main` 落后于当前分支，且有一个与当前分支重复的提交（“Centralize numeric standardization”）。不要在 `main` 上继续工作；需要时把当前分支合并或重置过去。
- `weights/supervisor-full-spec` 分支已经并入当前分支，已删除。
- 仓库没有配置远程推送记录，是否推送到哪里由接手方决定。

## 6. 已知问题

- `pipeline.yaml` 的默认 include 链仍是旧秘鲁区脚本，Secocha 和 Goslar 用的是独立 runner，没有接进 DAG。
- `bin/` 里部分津巴布韦脚本引用了已在 8 月清理掉的 `outputs/_archive/...` 文件，现在跑不起来（`export_v1_working_boundary.py`、`prepare_v1_multicriteria_evidence.py`、`plot_v1_boundary_paper.py`）。津巴布韦已是背景案例，影响不大。
- 一些旧字段名比实际证据宽泛，比如树冠覆盖下降只是植被损失代理指标。9 月的语义说明在 `goslar_abzucht_display_rectangle_v1/component_semantics_v1/` 和 `input_semantics_followup_v1/`。
- 部分原始数据因许可限制没有放进移交包（见移交包里的 `EXCLUSIONS.json`），历史重跑可能需要重新申请。
- 下载 CLMS 和 Sentinel 像元的脚本需要本机的访问凭据文件，凭据不在仓库里。

## 7. 下一步建议

1. 决定综合优先级指数怎么和洪水证据对照评估。如果要调权重，先留出一份独立的评估数据，不要用同一份数据既调权重又做验证。
2. 检查各准则的覆盖率和代理指标含义，缺数据的地方要在图上可见，不能当作低风险。
3. 把 Secocha 和 Goslar 的 runner 接进 `pipeline.yaml`，或者干脆让 `pipeline.yaml` 只服务这两条链，去掉旧秘鲁区默认链。
4. 在接手人的机器上重建环境，跑一遍测试和上面的主要命令，确认可复现。
5. 确认接手的人能打开 `outputs/` 里的 QGIS 审阅项目。

## 8. 本次精简做了什么（2026-10-08）

- 删除约 17 GB 重复和临时文件：`exports/` 里三个与 zip 完全相同的解压文件夹（zip 已逐文件核对），`tmp/`（8 月 PPT 中间版本，含一个网站 cookies 文件），`data/tmp/`，12 个 `*_previous_<时间戳>` 自动备份目录，根目录的 `IFPM_for_ChatGPT_QA.zip`，以及缓存和 `.DS_Store`。
- 删除 `bin/_archive/` 里 22 个废弃脚本和两张无用的生成图片（可从 Git 历史找回）。
- 重写 `outputs/README.md`，删除过时的 `outputs/OUTPUTS_INDEX.csv`；更新 `README.md`、`bin/README.md`、`context/README.md`。
- 参考论文移到 `context/references/`。

2026-10-09 补充精简 `context/`：只保留研究记录、数据登记、术语表、方法说明和 Supervisor 移交草稿，另外留下 `context/configs/`，因为 `bin/` 里的脚本要读取它。导师沟通稿、早期核查报告、旧计划和归档、下载前检查、参考网格规则、导师方法框架截图和最初的数据清单都已删除（Git 历史里可以找回）。参考论文 PDF 也已删除，它不在 Git 里。保留下来的研究记录里还有少数路径指向已删除的文件，这些是历史出处，需要时去 Git 历史里查。

2026-10-10 精简文档和代码里过时与防御性的内容：研究记录从 9 份合并成 `EXPERIMENTS.md` 和 `DECISION_LOG.md` 两份，只写当前实验和仍然有效的决定；`AGENTS.md` 从 467 行的 AI 管理规则改成一页纸的工作约定；术语表只保留当前准则和字段含义；删除 4 个只检查措辞的脚本（`check_*terminology*`、`check_glossary_sources`、`check_top20_priority_wording`）及对应测试；旧秘鲁区的图表配置移到 `bin/package/`。

2026-10-10 删除 `exports/IFPM_Supervisor_Handover_2026-10-08.zip`（14 GB，精简前的完整快照）及其校验文件，以及 8 月分享包和 6 月导师汇报包两个 zip。
