# PIM 转换流程 — 从原始数据到优先级地图

本文说明 Secocha 和 Goslar 两条链怎样从原始数据算出优先级地图（PIM）。具体数值以各输出目录里的 `run_manifest.json` 为准；代码入口是 `bin/factors/run_peru_secocha_chain.py`（Goslar 用同一套代码，入口是 `run_goslar_peru_style_chain.py`）。

## 1. 三层结构

```
原始数据                    组件 (0-1)                    主准则 (0-1)        PIM
SRTM/Copernicus DEM   →  twi_wetness, drainage_proximity ┐
CHIRPS / REGNIE 降雨   →  rainfall_climatology            ┴→ Flood     0.34 ┐
SoilGrids K           →  soil_k_factor                   ┐                 │
DEM 坡长坡度          →  ls_factor                        ├→ Sediment  0.25 │
WorldCover            →  c_factor                        ┘                 │
WorldCover / CLMS     →  land_cover_pressure,            ┐                 ├→ PIM (0-1)
                         bare_soil_vegetation_loss,      ├→ Land Use  0.17 │
                         built_agriculture_road_expansion┘                 │
WorldCover / 保护区    →  water_wetland, protected        ─→ Environmental 0.10
OSM / 人口 / 建筑      →  road_access, settlement_population,
                         critical_infrastructure          ─→ Socioeconomic 0.14 ┘
```

子权重见 `context/docs/research-map/DECISION_LOG.md`。采矿不进入计算，只在 PIM 算完后作为对照图层叠加。

## 2. 每一步的规则

**变成 0–1 的三种方式**
- 连续量（TWI、距离、LS、K、降雨、人口等）：取研究区内第 2 和第 98 百分位作为上下限，线性缩放并截断到 0–1。距离类指标再取 1 − 值，使“离得越近分越高”。
- 分类数据（WorldCover 土地类别）：按查表把每个类别映射成一个 0–1 值。
- 矢量范围（保护区、水体）：在范围内为 1，范围外为 0。

百分位缩放的结果是研究区内的相对排序，换研究区上下限就会变。Goslar 扩展区沿用原 Abzucht 区的上下限（“冻结锚点”），这样新旧区域的分数可以直接比较。

**加权求和**
- 组件按子权重加成主准则，主准则按顶层权重加成 PIM，每层权重之和为 1。
- 只有所有组件都有值的像元才计算分数。缺任何一项，该像元就是 NoData，不用 0 填补，也不把缺失组件的权重分给别的组件。
- Goslar 的部分旧分支例外：缺组件时按已有组件重新分配权重。相关实验的说明里已经注明。

**分级出图**：PIM 按 0.2 等间距分成五级，0.6 以上算“高”。0.6 只是显示用的分界，不是经过验证的洪水阈值。

## 3. 需要记住的局限

- CHIRPS 降雨的原始分辨率约 5 km，SoilGrids 是 250 m，对齐到 30 m 网格后精度并没有提高。
- 泥沙准则是侵蚀源的相对评分，不是土壤流失量（没有使用 R 因子）。
- 部分字段名比数据本身的含义宽，详见 `context/docs/glossary.md`。
- 地图空白处是缺数据，不是低风险。
