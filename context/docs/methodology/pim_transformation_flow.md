# PIM 转换流程详解 — 从原始参数到优先级地图

> **版本提示（2026-08-05，按 Supervisor 最后说明修正）：** 当前测试基线
> 保留原顶层权重 FH 0.35、SE 0.25、LU 0.20、ES 0.12、SV 0.08；只把
> Land Use 子组改为 0.40 LC + 0.35 BV + 0.25 BE。Mining 从 PIM 输入、
> Land Use 组合和 weighted overlay 中移除，仅在 PIM 完成后作为外部
> 叠加层。旧含 Mining 结果保存在 `01_legacy_with_mining/`，当前测试基线
> 保存在 `02_no_mining_test_baseline/`；0.34/0.25/0.17/0.10/0.14 版本已
> 降为 `04_no_mining_alternative_weights_034_025_017_010_014/` sensitivity
> alternative。本文主体中的旧 Mining 图示仍作为历史转换证据保留。

> 本文用真实的工程数值逐步解释秘鲁 Arequipa 工作区如何从原始输入
> 得到最终的五色优先级筛查地图（PIM）。所有权重、裁剪区间、覆盖率
> 均取自 `outputs/srtm_1arcsec_peru_pilot/` 下受治理的 CSV，
> 可与代码 `bin/_lib/ifpm_tools.py`、
> `bin/criteria/build_peru_hybas_l7_6070641200_criteria_stack.py`、
> `bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py`
> 一一对应。
>
> 声明级别：整条链为 `sensitivity_scenario`（最末层 PIM）与
> `provisional`（中间准则）。**不是**已验证的洪水风险图，**不是**
> 救援决策图。这是 AHP-MCDA 加权叠加筛查，不是水动力淹没模型。

## 0. 全局架构（三层叠加）

```
原始输入 (raw)          标准层 (0-1)              PIM 主准则 (0-1)            最终地图
─────────────          ─────────────             ──────────────              ─────────
SRTM DEM        ─┐
  → slope        │
  → TWI          ├─→  twi_wetness (0-1)      ─┐
  → flow acc     │                             │
  → drainage dist├─→  drainage_proximity(0-1) ├─→ Flood   (0-1)          ─┐
CHIRPS 降雨      └─→  rainfall_climatology(0-1)┘                          │
                                                                  ┌──────┴──────┐
SoilGrids K     ─→  soil_k_factor (0-1)     ─┐                       │             │
SRTM LS         ─→  ls_factor (0-1)          ├─→ Sediment (0-1)      ├─→ PIM      │
WorldCover C    ─→  c_factor (0-1)          ─┘      (K0.30/LS0.45/C0.25)│ (0-1)   │ → 五色图
                                                                  │   权重:     │   0-0.2
WorldCover 土地 ─→  land_cover_pressure(0-1) ─┐                     │   FH 0.35   │   0.2-0.4
INGEMMET 采矿点 ─→  mining_pressure (0-1)    ├─→ LandUse (0-1)      │   SE 0.25   │   0.4-0.6
                                          (L0.35/M0.65)│             │   LM 0.20   │   0.6-0.8
                                                                  │   ES 0.12   │   0.8-1.0
WorldCover 水/湿 ─→  water_wetland (0-1)     ─┐                     │   SV 0.08   │
SERNANP 保护区   ─→  protected_area (0-1)    ├─→ Environ. (0-1)     │             │
                                          (W0.60/P0.40)│             └──────┬──────┘
                                                                  ┌──────┴──────┐
OSM 道路         ─→  road_access (0-1)       ─┐                     │             │
WorldPop 人口    ─┐                          ├─→ Socioec.(0-1)      │             │
OSM 建筑        ─┴→ infrastructure(0-1)     ─┘ (R0.45/I0.55)        └─────────────┘
                                          (I=0.5人口+0.5建筑)
```

三类关键操作反复出现，下面先讲清这三条规则，再逐层展开。

---

## 1. 三条贯穿全流程的规则

### 规则 A：标准化（raw → 0-1）

**函数**：`normalize_2_98()`（`bin/criteria/...criteria_stack.py`），
等价于 `ifpm_tools.standardize(p_low=2, p_high=98)`。

公式：

```
low  = 第 2 百分位的值
high = 第 98 百分位的值
score = clip((x - low) / (high - low), 0, 1)
```

要点：
- **百分位裁剪**：极端的 2% 高值和 2% 低值被夹到 0/1，避免单个离群
  像元把整张图压扁。`low`/`high` 不是全局 min/max。
- **方向性 invert**：对"距离"类指标（离排水越近越危险），先正向标准化
  再 `score = 1 - score` 翻转，使"高值 = 高危险"语义统一。
- **NoData 保持 NoData**：无数据像元不填 0，不参与任何后续求和。
  这是硬性规则（`criteria_readiness_table.csv` 的 `nodata_policy`
  列统一为 `preserve NoData; no score imputation`）。

### 规则 B：加权求和（组件 → 主准则 / 主准则 → PIM）

**函数**：`combine_weighted_layers()`（子层）、
`combine_common_support_criteria()`（主层）。

```
combined = Σ (layer_i × weight_i)   仅在所有组件都有效的像元
```

要点：
- **共同支撑（common support）**：一个像元只有当某一层的**所有**组件
  都有有效值时才得分；任一组件缺数据，该像元就是 NoData。
  → 这就是为什么最终图上有 4.90% 空白。
- **权重和=1**：每层权重相加为 1，代码里 `if sum != 1.0: raise`。
- 不做权重重归一化（即缺数据时**不**把该组件权重分给别人）。

### 规则 C：claim_level 标注

每个产出的 0-1 栅格都带声明级别，进 PIM 之前是 `provisional`，
最终 PIM 是 `sensitivity_scenario`（因为权重来自导师直给、未做 CR 一致性检验）。

### 规则 D：0-1 栅格的三种来源（统计标准化 / 值函数 / 几何二值）

**重要**：并不是所有 0-1 栅格都是"标准化"的结果。流程里有**三种**把数据
变成 0-1 的方法，必须区分清楚——它们的方法论强度不同。

**证据（下载产品的真实值域，没有一个落在 0-1）**：

| 数据源 | 下载时的原始值域 | 物理含义 |
|---|---|---|
| SRTM DEM | 144.87 – 3188.34 | 高程（米） |
| CHIRPS 降雨 | 37.63 – 101.56 | mm / 雨季 |
| SoilGrids K | 0.1003 – 0.2661 | K 可蚀性（US customary） |
| WorldPop 人口 | 0.0003 – 78.99 | 每像元人口数 |

→ **没有任何数据源下载时就是标准化结果**。所有 0-1 转换都在本地完成。
但转换方法分三类：

| 方法 | 输入 | 输出 | 用在 | 方法论性质 |
|---|---|---|---|---|
| **统计标准化** | 连续物理量 | 0-1 | twi, drainage, ls, c_factor, rainfall, soil_k, road, mining, population | 2-98 百分位 min-max，数据驱动，可复现 |
| **值函数映射** | 离散分类码 | 0-1 | land_cover_pressure（WorldCover 类别→压力值）, c_factor 的类别查表 | 领域知识驱动，主观但可追溯 |
| **几何二值化** | 矢量边界 / 类别选择 | 0/1 | protected_area_context（SERNANP 多边形→在内=1）, water_wetland_context（选水/湿地类） | 几何判断，确定性 |

**为什么这很重要**：
- 统计标准化的 0-1 是**相对排序**（依赖区内分布），换研究区 clip 区间会变。
- 值函数的 0-1 是**领域判断**（如"裸地=高侵蚀压力"），换专家可能改映射。
- 几何二值的 0/1 是**客观事实**（在保护区内或不在），无歧义。

混合这三类会让"权重"和"标准化"的语义混乱。例如 `land_cover_pressure`
(值函数) 和 `c_factor` (查表) 都来自 WorldCover 但用了**不同的 0-1 映射逻辑**——
这就是为什么它们虽同源却是两个独立组件（`Spearman ρ=0.498`，不是 1.0）。

---

## 2. 第一层：原始输入 → 标准 0-1 层

下表是**真实数值**，来自 `standardization_notes.csv` 与
`criteria_readiness_table.csv`。结合规则 D 的三种 0-1 来源，每个组件标注了
**转换方法**与**在哪做**两个维度：

- **转换方法**：[统计] = 2-98 百分位标准化；[值函数] = 类别映射；
  [二值] = 几何判断。
- **在哪做**（仅对 [统计] 方法分两类）：✦ = `criteria_stack.py` 现场做；
  ⬆ = 上游脚本已做好（输入文件名带 `_0_1`，clip 区间在各自 metadata）。

| 组件 | 原始数据源 | 原始单位/范围 | clip low | clip high | invert? | 转换方法 | 在哪做 | 含义 |
|---|---|---|---|---|---|---|---|---|
| `twi_wetness` | SRTM DEM 派生 TWI | TWI 4.49–14.71+ | 4.491 | 14.711 | 否 | [统计] | ✦ 本脚本 | 高 TWI = 更湿 = 更易汇水 |
| `drainage_proximity` | DEM 派生水流距离 | 米 0–721+ | 0.0 | 721.25 | **是** | [统计] | ✦ 本脚本 | 离排水网越近分越高 |
| `rainfall_climatology` | CHIRPS 12–3 月雨季均值 | mm/季（~5km 有效） | 见 rainfall metadata | 见 rainfall metadata | 否 | [统计] | ⬆ `build_..._rainfall_criterion.py` | 高雨 = 高洪水 conditioning |
| `soil_k_factor` | SoilGrids 250m | K 0.1003–0.2661 | 见 soil_k metadata | 见 soil_k metadata | 否 | [统计] | ⬆ `build_..._soil_k_factor.py` | 高 K = 更易侵蚀（250m 有效） |
| `ls_factor` | SRTM 派生坡长×坡度 | LS 0–50（封顶） | 0.094 | 21.145 | 否 | [统计] | ✦ 本脚本 | 高 LS = 更强侵蚀势 |
| `c_factor` | WorldCover 派生 RUSLE C | C 0.003–0.70 | 0.003 | 0.700 | 否 | [统计] | ✦ 本脚本 | 高 C = 更易侵蚀 |
| `land_cover_pressure` | WorldCover 土地利用分类 | 离散类别码 | — | — | 否 | [值函数] | ⬆ WorldCover 派生脚本 | 与 C 同源但用领域映射，非统计 |
| `mining_pressure` | INGEMMET 小矿点 | 距离(米) | 见 proximity metadata | 见 proximity metadata | **是** | [统计] | ⬆ `build_..._osm_proximity_criteria.py` | 离官方小矿点越近分越高 |
| `road_access_proximity` | OSM 道路 | 距离(米) | 见 proximity metadata | 见 proximity metadata | **是** | [统计] | ⬆ `build_..._osm_proximity_criteria.py` | 离路越近 = 更高暴露 |
| `water_wetland_context` | WorldCover 水/湿地类 | 类别选择 | — | — | — | [二值] | ⬆ Environmental 上游脚本 | 选水/湿地类=1，环境敏感上下文 |
| `protected_area_context` | SERNANP 国家保护区层 0 | 矢量多边形 | — | — | — | [二值] | ⬆ Environmental 上游脚本 | 在保护区内=1；区内无几何→贡献 0 |

> **[统计] 标注的 9 个组件**才是真正的"标准化"，统一方法 2-98 百分位 min-max，
> 区别只在 ✦ 本脚本 / ⬆ 上游。`standardization_notes.csv` 只有 4 行，
> 因为它是 `criteria_stack.py` 的自产诊断文件，只记 ✦ 那 4 个；
> ⬆ 的 5 个 clip 区间在各自上游脚本的 metadata CSV。
>
> **[值函数] 和 [二值] 的 3 个组件不是标准化**，是领域映射 / 几何判断，
> 没有 clip 区间可言（故标"—"）。

### 单像元示例（LS-factor 一条龙）

挑一个坡度较陡的像元，看它如何贯穿：

```
原始 DEM 高程      → slope (度)     → LS = f(slope, 坡长)
                     (例如 18°)        (例如 LS = 12.3)

标准化：
  score = clip((12.3 - 0.094) / (21.145 - 0.094), 0, 1)
        = clip(12.206 / 21.051, 0, 1)
        = 0.580

→ ls_factor_0_1 = 0.580   （这一像元在 LS 维度上偏高）
```

这个 0.580 随后进 Sediment 主准则。

---

## 3. 第二层：标准 0-1 → 五个 PIM 主准则

权重来自 `pim_subcriteria_weights.csv`，全部 `implemented`。

### Flood Hazard（洪水）
```
Flood = 0.40 × rainfall_climatology
      + 0.30 × twi_wetness
      + 0.30 × drainage_proximity
```
语义：高雨 + 高湿 + 近排水 = 高洪水 conditioning。三者共同支撑。

### Sediment（沉积/侵蚀源）
```
Sediment = 0.30 × soil_k_factor
         + 0.45 × ls_factor       ← 最大权重，地形驱动
         + 0.25 × c_factor
```
**注意**：这是相对侵蚀源**优先级指标**，不是 USLE A 绝对土壤流失量
（R-factor 已隔离出关键路径）。K 有效分辨率仍是 250m。

### Land Use / ASM（土地利用/采矿压力）
```
LandUse = 0.35 × land_cover_pressure
        + 0.65 × mining_pressure   ← 主导
```
INGEMMET 小矿点是官方点源证据（非卫星 footprint）。

### Environmental（环境敏感）
```
Environmental = 0.60 × water_wetland_context
              + 0.40 × protected_area_context
```
**当前现实**：检查过的 SERNANP 国家层 0 在 Arequipa 工作区 +5km 内无几何，
所以保护区组件贡献为 0 → 整个 Environmental 实际是水/湿地主导。
均值仅 0.407，最高 0.6（永远到不了 1）。

### Socioeconomic（社会经济暴露）
```
Socioeconomic = 0.45 × road_access_proximity
              + 0.55 × infrastructure_exposure
```
其中 `infrastructure_exposure` 上游再分：
```
infrastructure = 0.50 × WorldPop 人口 + 0.50 × OSM 建筑   (placeholder)
```
**注意**：道路虽只占 0.45 权重，但因与暴露共变，道路贡献了加权空间均值的
94.4%——这是共变诊断，**不是**有效权重，不能据此重调导师给的 AHP。

---

## 4. 第三层：五个主准则 → 最终 PIM

```
PIM = 0.35 × Flood        (FH)
    + 0.25 × Sediment      (SE)
    + 0.20 × LandUse       (LM)
    + 0.12 × Environmental (ES)
    + 0.08 × Socioeconomic (SV)
                            和 = 1.00
```

- **权重来源**：2026 年 7 月导师直给秘鲁权重，**无**配套 pairwise 矩阵、
  **无** CR 一致性比 → 因此声明为 `sensitivity_scenario`，不是最终权重。
- **共同支撑门**：五个主准则全部有效的像元才得分。
  `MIN_SCOREABLE_VALID_FRACTION = 0.95`，实测 95.0998%。
- **边界裁剪**：边界外像元强制 `NaN`（`score[~boundary_mask] = nan`）。

### 最终 PIM 五分类（成图用）

| 类 | 区间 | 颜色 | 含义 |
|---|---|---|---|
| very_low | 0.0–0.2 | 浅黄 | 最低优先级 |
| low | 0.2–0.4 | 黄 | |
| moderate | 0.4–0.6 | 橙 | |
| high | 0.6–0.8 | 红 | |
| very_high | 0.8–1.0 | 深红 | 最高优先级筛查区 |

最高优先级五分位（top 20%）= **521.356 km²** 被选中。

---

## 5. 为什么图上有空白？— 数据缺口分解

总边界内 4.9002% 像元未评分，来自 `classify_evidence_support()`
分出的 support 类：

| support 类 | 含义 | 占比 |
|---|---|---|
| 1 | 五准则共同支撑，已评分 | 95.0998% |
| 2 | 缺 LS（hillslope 通道掩膜保留） | 3.7573% |
| 3 | 缺 K（SoilGrids 源边缘） | 1.1326% |
| 4 | 其他/边界内但组件不全 | 0.0103% |

**关键**：这些空白**不填 0**（0 会变成"低风险"，错误）、**不重分配权重**。
成图时用阴影线 `////` 覆盖标出，明示是数据缺口而非低风险。
这是 `criteria_evidence_count.tif` 与 `evidence_support_class.tif`
驱动的。

---

## 6. 一张图串完全流程（用于 PPT 的核心示意）

```
[1] 原始栅格          [2] 标准化 0-1          [3] 主准则 0-1         [4] PIM 0-1           [5] 五色图
                                                                                          
 SRTM DEM ────────→ slope/TWI/drain ──→  Flood ─────────┐
                                            (0.35)       │
 SoilGrids/LS/C ──────────────────────→  Sediment ──────┤
                                            (0.25)       ├─→ PIM ──→ 五色
 WorldCover/INGEMMET ─────────────────→  LandUse ───────┤          0-0.2 浅黄
                                            (0.20)       │          ...
 WorldCover/SERNANP ───────────────────→  Environmental ─┤          0.8-1.0 深红
                                            (0.12)       │
 OSM/WorldPop ────────────────────────→  Socioeconomic ─┘
                                            (0.08)
        ↑                  ↑                  ↑              ↑               ↑
   真实物理量        2-98 百分位裁剪         加权求和         五主准则加权      equal-interval
   (m, 度, mm)       + invert 翻转          共同支撑         共同支撑          五分类
                      NoData 保持           缺组件=NoData    95.1% 可评分      4.9% 阴影线
```

---

## 7. QGIS 成图部分（与 PPT 第二节呼应）

成图不只是渲染颜色，还有一套样式与可移植规则：

### 栅格样式（`.qml`）
每个栅格层配一个 `.qml` 样式文件。当前独立包位于
`exports/qgis_packages/<site>/<FullAudit|ReviewMap>/styles/`；旧 Peru/Zimbabwe
合并包只读归档在
`exports/qgis_packages/_archive/legacy_peru_zimbabwe_combined/`。
关键统一规则：
- **NoData → 透明**：所有 PIM 相关栅格的 NoData 设为透明，避免把"无数据"
  误显示成"低风险绿色"。
- **色带语义**：优先级用发散色（红=高/黄=低），因子用顺序色
  （如降雨单色渐变），上下文证据用分类色。
- **claim_level 元数据**：样式与 `manifest.csv` 的 `claim_level` 列一致。

### 图层组织（4 组）
QGIS 工程按语义分四组打开：
1. **Priority result** — 最终 PIM（默认可见）
2. **Five PIM criteria** — 五个主准则（默认关）
3. **Input and derived factors** — 原始与派生因子（默认关）
4. **Context and evidence** — 人口、采矿点、SINPAD、边界

### 可移植性
包是自包含的：`manifest.csv` 记录每个层的
`portable_source_path` + `portable_sha256`，导师可在自己 QGIS 打开
`.qgz` 并核对任意层的哈希。这把"可信"从"我说算"变成"你可查"。

---

## 8. 待确认的内容选择（写给下一步）

这份说明覆盖了全部转换。落地到 PPT 时需要决定：

1. **深度**：是把上面 1–6 节全部做成幻灯片（约 6–8 张方法页），
   还是只取第 1、4、6 节做精简版（3 张）？
2. **单像元示例**：要不要真的从栅格里取一个真实像元的数值贯穿全链
   （需要读一个具体像元的 raw → standardized → weighted 值）？
3. **QGIS 截图**：用现有的 `layer_qa/peru_layer_contact_sheet.png`，
   还是重新从 QGIS 渲染工程界面截图？

确认后即可按 Block 0（数值核对表）→ Block 1–4（幻灯片）→ Block 5（装配）执行。
