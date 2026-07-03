# Mentor Teams Messages

For Microsoft Teams chat. Send one message at a time. Suggested order below.

**English** = paste this to the mentor. **中文** = your reference.

---

## Send first

### 1. Scope

**EN:**

> Quick scope check — if we can't get external data (mining records, validation, Peru), is a Zimbabwe-only terrain-based priority map enough for the thesis? Or are those must-haves?

**中文:** 范围确认下——如果外部数据（采矿、验证、秘鲁）拿不到，只做津巴布韦地形的优先级图够不够做论文？还是这些必须有？

### 2. Data you can share

**EN:**

> For Upper Mzingwane, do you have or can you get any of these?
> - catchment boundary file
> - historical flood records
> - mining / ASM site data
> - contacts at ZINWA / Geological Survey / EMA

**中文:** Upper Mzingwane 这些您有吗，或能要到吗？流域边界文件、历史洪水记录、采矿/ASM 数据、ZINWA/地调局/EMA 联系人。

### 3. AHP weights

**EN:**

> AHP weights — will you fill in the comparison matrix yourself, or should I prep it for an expert? Or will weights not be ready this term?

**中文:** AHP 权重——您自己填比较矩阵，还是我准备给专家？还是这学期来不及？

---

## Send when the first three are answered

### 4. Boundary

**EN:**

> Can I set V1 (~3690 km², HydroBASINS) as the final study area? Or will you send me a boundary file?

**中文:** V1（约 3690 km²，HydroBASINS）能直接定为最终研究区吗？还是您会给我边界文件？

### 5. First map approach

**EN:**

> First version — terrain-only scoring, rainfall as background info. OK? Rainfall won't drive the score that way.

**中文:** 第一版——只用地形打分，降雨当背景信息，行吗？这样降雨不参与评分。

### 6. Defaults check

**EN:**

> A few defaults — OK with these?
> - hydrology: fill sinks + D8 flow direction
> - soil loss: Fournier index + SoilGrids + WorldCover
> - AHP consistency cutoff: CR < 0.1
> Tell me if any should change.

**中文:** 几个默认值确认——这些都行吗？水文（填洼+D8）、土壤侵蚀（Fournier+SoilGrids+WorldCover）、AHP 一致性（CR<0.1）。哪个要改告诉我。

---

## Only if needed

### 7. Validation (only if #1 said required)

**EN:**

> If validation is needed — start with public data (EM-DAT, GloFAS), or can you get local flood records?

**中文:** 如果要验证——先上公开数据（EM-DAT、GloFAS），还是您能弄到本地洪水记录？

### 8. Criteria (only if mining or soil data unavailable)

**EN:**

> If we can't get mining or soil data — OK to drop those two and score flood / terrain / land-use / social only?

**中文:** 采矿和土壤数据拿不到的话——去掉这两项，只评洪水/地形/土地利用/社会，行吗？

---

## Attachments Cheat-Sheet (What To Send With Each Message)

One image per message max. Drag-drop the PNG into Teams. Images beat documents for quick
decisions. Skip the attachment where it says "none".

| Msg | Attach this file | Why |
|---|---|---|
| 1 Scope | `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png` | Shows what evidence exists vs missing — mentor sees the full picture at once |
| 2 Data | `outputs/v1_multicriteria_evidence_package/panel_c_v1_exposure_mining_indicator.png` | Shows mining evidence is thin (only 2 OSM mining indicators) — motivates the ask |
| 3 AHP | none (if mentor wants the form, send `AHP_Elicitation_Protocol_And_Template_2026-06-15.md`) | Factual question; the 7 criteria are listed in the message |
| 4 Boundary | `outputs/v1_working_boundary/v1_boundary_diagnostic.png` | Shows V1 on a map: Mzingwane Dam + Esigodini inside, Gwanda outside |
| 5 Map approach | `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.png` | Shows what terrain-only scoring actually produces |
| 6 Defaults | none | Pure confirmation; mentor just says OK or flags an item |
| 7 Validation | none (facts are in the message) | Mentor either has local records or not |
| 8 Criteria | `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png` (same as #1) | Shows which criteria have evidence — supports dropping weak ones |

Optional short text companions (if the mentor wants one-paragraph context, not a pile of docs):

- For msg 1 / 8: `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_caption.md`
- For msg 5: `outputs/v1_terrain_mentor_package/mentor_v1_terrain_caption.md`
- For msg 4: `outputs/v1_working_boundary/v1_boundary_paper_caption.md`

These caption files are 1-paragraph summaries written for mentor review, not long reports.

## Notes

- Data processing does not wait for these answers. I keep working on already-downloaded data
  regardless.
- These questions only decide how to label outputs and what extra data to ask for.
- Full detail per decision: `Mentor_Decision_Briefing_2026-06-15.md`.
