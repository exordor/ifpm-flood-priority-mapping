#!/usr/bin/env python3
"""Build a complete, purpose-labelled inventory of the local outputs tree."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"
REPORT_DIR = OUTPUTS / "project_checks/output_inventory_2026-08-18"


# Status is about present-day use, not scientific validity.
DIRECTORIES: dict[str, tuple[str, str, str, str]] = {
    "[root]": ("目录索引", "outputs 根目录说明、历史索引和小型规划记录", "不进入评分", "保留说明；隐藏文件可清理"),
    "boundary_v1": ("冻结基线", "Zimbabwe Upper Mzingwane 旧版准则、降雨和优先级工作流", "历史比较/方法溯源", "保留，只读"),
    "chirps_v3_zimbabwe_prototype": ("冻结基线", "Zimbabwe CHIRPS 降雨比较和图件", "粗分辨率降雨背景", "保留，只读"),
    "esa_worldcover_2021_goslar": ("Goslar 当前链", "Goslar WorldCover/CLMS 土地覆盖与 C-factor 派生层", "进入或解释土地覆盖准则", "保留"),
    "esa_worldcover_2021_peru_pilot": ("冻结基线", "旧 Peru pilot 的 WorldCover/C-factor", "旧 Peru 土地覆盖准则输入", "保留，只读"),
    "esa_worldcover_2021_v1_methodology": ("冻结基线", "Zimbabwe V1 WorldCover/C-factor", "旧方法输入", "保留，只读"),
    "geofabrik_osm_peru_pilot": ("冻结基线", "旧 Peru pilot 的 OSM 道路和采矿邻近指标", "旧代理指标", "保留，只读"),
    "goslar_2017_satellite_validation": ("Goslar 验证", "2017 前后 Sentinel-2 水体候选变化", "L2 独立一致性证据，不进入评分", "保留"),
    "goslar_focus_boundary": ("Goslar 当前链", "Goslar layout focus extent 边界", "裁剪和展示范围，不是流域", "保留"),
    "goslar_harz_2024_focus_area": ("Goslar 验证", "焦点区来源登记、事件证据和位置图", "范围/事件上下文", "保留"),
    "goslar_l2_independent_consistency": ("Goslar 验证", "Goslar L2 独立一致性统计结果", "支持 L2 证据等级，不进入 PIM", "保留"),
    "goslar_mining_context_overlay": ("Goslar 上下文", "LBEG/OSM mining context overlay", "外部背景图层，权重 0", "保留"),
    "goslar_official_hydrology_and_flood_data": ("Goslar 验证", "官方水文边界和 HWRM 洪水情景边界", "外部验证/范围背景，不进入评分", "保留"),
    "goslar_qgis_project_package": ("Goslar 交付", "Goslar FullAudit 工作区 QGIS 包、样式和 QA", "审计项目源；正式发送使用 exports 包", "保留"),
    "goslar_qgis_project_package_compact": ("Goslar 交付", "Goslar ReviewMap 工作区 QGIS 包", "精简审阅项目源", "保留"),
    "goslar_sentinel_bare_soil_candidate": ("Goslar 支持", "Sentinel-2 裸土频率和 NDVI 变化候选层", "土地覆盖升级诊断", "保留"),
    "hydrosheds_boundary_decision": ("历史方法", "Upper Mzingwane 边界候选诊断", "边界选择溯源", "保留，小文件"),
    "indeci_sinpad_peru_flood_events": ("冻结基线", "旧 Peru 区域 SINPAD 洪灾事件摘要", "历史事件上下文", "保留，只读"),
    "inei_peru_poverty_2018": ("冻结基线", "INEI Arequipa 贫困数据登记", "旧社会经济来源记录", "保留，只读"),
    "ingemmet_catastro_minero_peru_pilot": ("冻结基线", "旧 Peru pilot 官方采矿权压力层", "旧 mining-pressure 输入", "保留，只读"),
    "mapbiomas_peru_collection3_change_pilot": ("Secocha 支持", "MapBiomas 多期土地变化对齐与指标", "土地变化候选/敏感性证据", "保留"),
    "mentor_voi_rainfall_intake": ("历史方法", "导师提供降雨档案的结构和字段盘点", "来源溯源", "保留，小文件"),
    "methodology_figures": ("方法说明", "可编辑方法流程图及导出图", "报告/论文方法说明", "保留；可清理隐藏备份"),
    "peru_boundary_discovery": ("冻结基线", "旧 Peru 边界发现与拓扑检查", "选址过程溯源", "保留，只读"),
    "peru_gap_closure_analysis": ("冻结基线", "旧 Peru 人口/SINPAD 与 PIM 共位分析", "旧数据缺口分析", "保留，只读"),
    "peru_integrated_briefing_board": ("报告支持", "Peru 综合汇报板", "旧区域汇报图", "保留，只读"),
    "peru_pilot_boundary": ("冻结基线", "旧 southern Peru pilot 边界及预检", "旧比较范围", "保留，只读"),
    "peru_report_figure_chain": ("报告支持", "Peru 因子到结果的报告图链", "旧 Peru 图件", "保留，只读"),
    "peru_scope": ("Secocha 当前链", "当前 Peru/Secocha 研究区激活与覆盖审计", "控制实际研究范围", "保留"),
    "peru_secocha_a7367_reference_extent_v1": ("Secocha 当前链", "Secocha 五准则、输入和优先级完整输出", "当前 Secocha provisional PIM 主目录", "保留"),
    "peru_secocha_boundary": ("Secocha 当前链", "Secocha active reference extent 边界", "裁剪与参考范围", "保留"),
    "peru_secocha_qgis_project_package": ("Secocha 交付", "Secocha FullAudit 工作区 QGIS 包", "审计项目源；正式发送使用 exports 包", "保留"),
    "peru_secocha_qgis_project_package_compact": ("Secocha 交付", "Secocha ReviewMap 工作区 QGIS 包", "精简审阅项目源", "保留"),
    "pim_environmental_sensitivity": ("历史方法", "早期 environmental sensitivity 汇总", "方法溯源，不是当前结果", "可后续归档"),
    "presentation_assets": ("汇报材料", "QGIS 截图、GeoTIFF 和拼图素材", "PPT 制作输入", "保留当前使用素材"),
    "presentation_previews": ("汇报材料", "当前可编辑 PPT、渲染页和 contact sheet", "演示稿 QA", "保留"),
    "project_checks": ("工程 QA", "术语、清单和全项目检查报告", "工程审计，不进入评分", "保留"),
    "secocha_2023_validation": ("Secocha 验证", "2023 事件证据、地点、卫星处理和对比图", "provisional 验证证据，不进入 PIM", "保留"),
    "slide_ready_figures": ("汇报材料", "可直接用于幻灯片的优先级、准则和 overlay 图", "汇报/附录图件", "保留"),
    "soilgrids_250m_peru_pilot": ("冻结基线", "旧 Peru SoilGrids K-factor", "旧土壤侵蚀输入", "保留，只读"),
    "soilgrids_250m_sediment_candidate": ("冻结基线", "Zimbabwe SoilGrids K-factor 候选", "旧侵蚀因子输入", "保留，只读"),
    "srtm_1arcsec_goslar": ("Goslar 当前链", "Goslar 地形、水文、五准则和 priority 输出", "当前 diagnostic_only PIM 主目录；目录名为历史兼容", "保留"),
    "srtm_1arcsec_peru_pilot": ("冻结基线", "旧 Peru pilot 全套地形、准则和场景", "已冻结，不是当前 Secocha 主线", "保留，只读"),
    "srtm_1arcsec_zimbabwe_prototype": ("冻结基线", "Zimbabwe 地形、水文和侵蚀派生层", "旧区域比较基线", "保留，只读"),
    "v1_working_boundary": ("冻结基线", "Upper Mzingwane frozen working boundary 与图件", "旧 Zimbabwe 空间范围", "保留，只读"),
    "worldpop_peru_population": ("冻结基线", "WorldPop Peru 子集登记", "旧人口来源记录", "保留，只读"),
    "zimbabwe_geoportal_subcatchments_2025": ("冻结基线", "Zimbabwe Geoportal 与 HydroBASINS 重叠摘要", "旧边界溯源", "保留，只读"),
    "zimbabwe_integrated_briefing_board": ("报告支持", "Zimbabwe 综合汇报板", "旧区域汇报图", "保留，只读"),
    "zimbabwe_report_figure_chain": ("报告支持", "Zimbabwe 因子到结果的报告图链", "旧 Zimbabwe 图件", "保留，只读"),
}


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError


def file_role(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == ".qgz":
        return "QGIS 项目文件"
    if suffix == ".qml":
        return "QGIS 图层样式"
    if "manifest" in name or "lineage" in name or "registry" in name:
        return "来源/运行清单"
    if "diagnostic" in name or "qa" in name or "check" in name or "coverage" in name:
        return "质量检查/诊断"
    if suffix in {".tif", ".tiff"}:
        return "栅格输入、派生层或评分结果"
    if suffix in {".gpkg", ".geojson"}:
        return "矢量边界、事件或上下文图层"
    if suffix in {".png", ".pdf", ".svg", ".webp"}:
        return "地图、图表或渲染预览"
    if suffix in {".csv", ".json", ".xml", ".ndjson"}:
        return "结构化结果、参数或检查记录"
    if suffix in {".md", ".txt"}:
        return "说明、结论或交接记录"
    if suffix in {".pptx", ".xlsx", ".drawio"}:
        return "可编辑交付材料"
    if suffix == ".bkp" or name.startswith("."):
        return "隐藏文件或编辑器备份"
    return "其他生成文件"


def main() -> None:
    generated = datetime.now(timezone.utc).isoformat()
    files = sorted(
        path
        for path in OUTPUTS.rglob("*")
        if path.is_file() and REPORT_DIR not in path.parents
    )
    top_dirs = ["[root]", *sorted(path.name for path in OUTPUTS.iterdir() if path.is_dir())]
    missing = sorted(set(top_dirs) - set(DIRECTORIES))
    if missing:
        raise RuntimeError(f"Unclassified output directories: {missing}")

    rows: list[dict[str, object]] = []
    for path in files:
        relative = path.relative_to(ROOT)
        top = relative.parts[1] if len(relative.parts) > 2 else "[root]"
        group, purpose, scoring_relation, retention = DIRECTORIES[top]
        stat = path.stat()
        rows.append(
            {
                "path": relative.as_posix(),
                "top_directory": top,
                "group": group,
                "file_role": file_role(path),
                "directory_purpose": purpose,
                "scoring_or_evidence_role": scoring_relation,
                "retention": retention,
                "extension": path.suffix.lower() or "[none]",
                "size_bytes": stat.st_size,
                "size_human": human_size(stat.st_size),
                "modified_local": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            }
        )

    summary: list[dict[str, object]] = []
    by_top: dict[str, list[dict[str, object]]] = {name: [] for name in top_dirs}
    for row in rows:
        by_top[str(row["top_directory"])].append(row)
    for top in top_dirs:
        group, purpose, scoring_relation, retention = DIRECTORIES[top]
        size = sum(int(row["size_bytes"]) for row in by_top[top])
        summary.append(
            {
                "directory": top,
                "group": group,
                "purpose": purpose,
                "scoring_or_evidence_role": scoring_relation,
                "retention": retention,
                "file_count": len(by_top[top]),
                "size_bytes": size,
                "size_mib": round(size / 1024 / 1024, 2),
                "size_human": human_size(size),
            }
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORT_DIR / "all_output_files.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = REPORT_DIR / "output_directory_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    total_bytes = sum(int(row["size_bytes"]) for row in rows)
    groups = Counter(str(row["group"]) for row in summary)
    largest = sorted(summary, key=lambda row: int(row["size_bytes"]), reverse=True)
    md = [
        "# IFPM outputs 文件与用途清单",
        "",
        f"生成时间：{generated}",
        "",
        f"当前 `outputs/` 共 **{len(rows):,} 个文件**、**{human_size(total_bytes)}**，分布在 **{len(summary)} 个一级目录**。",
        "完整逐文件明细见 `all_output_files.csv`；以下表格用于快速判断目录作用和保留策略。",
        "",
        "## 一级目录用途",
        "",
        "| 目录 | 类别 | 文件数 | 大小 | 作用 | 与评分/证据关系 | 建议 |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in sorted(summary, key=lambda item: (str(item["group"]), str(item["directory"]))):
        md.append(
            f"| `{row['directory']}` | {row['group']} | {row['file_count']} | {row['size_human']} | "
            f"{row['purpose']} | {row['scoring_or_evidence_role']} | {row['retention']} |"
        )
    md.extend(["", "## 空间占用最大的目录", ""])
    for index, row in enumerate(largest[:10], 1):
        md.append(f"{index}. `{row['directory']}` — {row['size_human']} / {row['file_count']} files")
    md.extend(
        [
            "",
            "## 阅读规则",
            "",
            "- `Goslar 当前链` 与 `Secocha 当前链`：模型计算或范围控制的当前输出。",
            "- `验证`、`上下文`：用于独立证据或地图解释；除非清单明确说明，不进入 PIM。",
            "- `交付`：工作区 QGIS 构建结果；真正发送给对方的是 `exports/qgis_packages/`。",
            "- `冻结基线`：保留用于历史比较和复现，不应继续写入或当成当前 Secocha/Goslar 结果。",
            "- 本清单描述文件用途，不把 diagnostic/provisional 输出升级为最终洪水风险结论。",
            "",
            f"文件类型统计：{dict(Counter(str(row['extension']) for row in rows).most_common())}",
            f"目录类别统计：{dict(groups)}",
        ]
    )
    (REPORT_DIR / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    chart_labels = {
        "srtm_1arcsec_peru_pilot": "Peru pilot (frozen)",
        "peru_secocha_a7367_reference_extent_v1": "Secocha A7367",
        "srtm_1arcsec_zimbabwe_prototype": "Zimbabwe prototype",
        "goslar_2017_satellite_validation": "Goslar 2017 validation",
        "ingemmet_catastro_minero_peru_pilot": "Peru INGEMMET",
    }
    top_chart = [
        dict(row, rank=index + 1, chart_label=chart_labels.get(str(row["directory"]), str(row["directory"])))
        for index, row in enumerate(largest[:6])
    ]
    composition = [
        {
            "label": chart_labels.get(str(row["directory"]), str(row["directory"])),
            "size_mib": row["size_mib"],
            "directory": row["directory"],
            "file_count": row["file_count"],
        }
        for row in largest[:5]
    ]
    composition.append(
        {
            "label": "Other outputs",
            "size_mib": round(sum(int(row["size_bytes"]) for row in largest[5:]) / 1024 / 1024, 2),
            "directory": "all remaining directories",
            "file_count": sum(int(row["file_count"]) for row in largest[5:]),
        }
    )
    source = {
        "id": "outputs_inventory",
        "label": "IFPM outputs filesystem inventory",
        "path": "outputs/project_checks/output_inventory_2026-08-18/output_directory_summary.csv",
        "query": {
            "engine": "DuckDB",
            "language": "sql",
            "sql": "SELECT * FROM read_csv_auto('output_directory_summary.csv')",
            "description": "Read the generated top-level outputs directory inventory.",
            "tables_used": ["output_directory_summary.csv"],
            "filters": ["regular files under outputs only", "inventory report files excluded"],
            "metric_definitions": [
                "file_count is the count of regular files below each top-level output directory",
                "size_mib is the sum of file sizes divided by 1024^2",
            ],
        },
    }
    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "IFPM outputs 文件与用途清单",
            "description": "当前 outputs 目录的用途、状态、空间占用和保留建议。",
            "generatedAt": generated,
            "sources": [source],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# IFPM outputs 文件与用途清单"},
                {
                    "id": "technical-summary",
                    "type": "markdown",
                    "sourceId": "outputs_inventory",
                    "body": (
                        f"## 当前输出以旧 Peru pilot 基线为主要空间占用\n\n"
                        f"盘点覆盖 **{len(rows):,} 个文件、{human_size(total_bytes)}、{len(summary)} 个一级目录**。"
                        "Goslar 与 Secocha 当前链、验证证据、QGIS 工作区包均已单独标注；冻结基线保留用于复现，"
                        "不能当作当前模型结果。"
                    ),
                },
                {
                    "id": "size-finding",
                    "type": "markdown",
                    "sourceId": "outputs_inventory",
                    "body": "## 存储高度集中在少数冻结基线目录\n\n下图显示空间占用构成，`README.md` 的 Top 10 排名和 `output_directory_summary.csv` 提供精确值。是否删除仍取决于复现和历史比较需要。",
                },
                {"id": "size-chart", "type": "chart", "chartId": "storage_composition"},
                {
                    "id": "usage-guide",
                    "type": "markdown",
                    "body": "## 使用指南与限制\n\n**查明细：** `README.md` 和 `output_directory_summary.csv` 列出全部一级目录；`all_output_files.csv` 列出 1,134 个文件。\n\n**看当前模型：** Goslar 使用 `srtm_1arcsec_goslar/`，Secocha 使用 `peru_secocha_a7367_reference_extent_v1/`；四个 `*_qgis_project_package*` 是工作区项目，对外交付在 `exports/qgis_packages/`。\n\n**看历史基线：** `srtm_1arcsec_peru_pilot/`、`boundary_v1/` 与 Zimbabwe prototype 只读保留。是否继续保留约 898 MiB 的 Peru pilot，应由复现需求决定。\n\n**口径：** 递归统计 `outputs/` 普通文件，不含 `data/` 和 `exports/`。目录用途不能替代各 raster/manifest 的科学声明；新增未分类目录会使盘点脚本失败。",
                },
            ],
            "cards": [],
            "charts": [
                {
                    "id": "storage_composition",
                    "title": "outputs 空间占用构成",
                    "subtitle": "五个最大一级目录与其余目录合计，MiB",
                    "type": "pie",
                    "intent": "composition",
                    "dataset": "storage_composition",
                    "sourceId": "outputs_inventory",
                    "encodings": {
                        "x": {"field": "label", "type": "nominal", "label": "目录"},
                        "y": {"field": "size_mib", "type": "quantitative", "label": "MiB", "unit": "MiB"},
                        "tooltip": [
                            {"field": "directory", "type": "text", "label": "目录"},
                            {"field": "file_count", "type": "quantitative", "label": "文件数"},
                        ],
                    },
                    "valueFormat": "number",
                    "unit": "MiB",
                    "maxRows": 6,
                }
            ],
            "tables": [],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": generated,
            "status": "ready",
            "datasets": {
                "headline": [{"file_count": len(rows), "size_mib": round(total_bytes / 1024 / 1024, 2), "directory_count": len(summary)}],
                "largest_directories": top_chart,
                "storage_composition": composition,
                "directory_summary": summary,
            },
        },
        "sources": [source],
    }
    (REPORT_DIR / "artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"files": len(rows), "directories": len(summary), "bytes": total_bytes, "report_dir": str(REPORT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
