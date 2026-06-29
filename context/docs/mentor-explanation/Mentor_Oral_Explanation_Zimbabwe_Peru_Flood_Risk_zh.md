# 给 Mentor 的口头说明稿：津巴布韦与秘鲁洪水风险研究

> 说明：这份口述稿写于早期（2026-06-10），在降雨侵蚀力（R 因子）调查之前。它仍然只
> 反映数据清单和方法框架阶段，没有涵盖 R 因子结论、自主原型，或当前的准则。当前状态
> 请看较新的 `Mentor_Trip_Data_Request_Package_2026-06-29.md` 和 R 因子简报。这里仅作为
> 早期清单讨论的口述辅助保留。

这份文档用于和 mentor 开会或当面沟通时口头说明，不是技术报告。目标是把 research review 的核心内容讲清楚：我做了什么、回应了 mentor 哪些要求、还有哪些问题需要她确认。

## 1. 核心意思

可以用一句话说明：

> 我对原始 dataset inventory 和 AHP-MCDA 方法框架做了 review，重点检查数据源是否可用、是否适合 Zimbabwe 和 Peru 的比较研究，以及在正式建模前还需要确认哪些方法问题。

最重要的结论是：

> 这个框架已经可以发给 mentor 做方法反馈，但还不能直接当作最终建模方案。正式建模前，还需要确定空间分析单元、时间范围、验证数据、数据访问限制，以及 AHP 权重制定流程。

## 2. 两分钟口头说明

可以这样开始：

> Thank you for sending the inventory. I reviewed it based on the points you mentioned: dataset availability and suitability, GIS preprocessing, AHP-MCDA weighting, mining and rehabilitation criteria, and remaining gaps before modelling.

然后概括整体判断：

> Overall, the structure is appropriate. The document already covers the main parts needed for this comparative flood-risk study, including flood hazard, sediment risk, land cover, mining disturbance, environmental sensitivity, socioeconomic exposure, rehabilitation potential, and validation.

再说明我补充了什么：

> In the review, I added official dataset links, checked the suitability of the main data sources, and separated sources that are directly open from sources that may need registration, licence acceptance, account access, or further manual verification.

然后主动说明限制：

> The public links have been manually checked and can be opened, but this does not yet mean that every dataset has already been downloaded, that all licences are cleared, or that every layer is GIS-ready.

最后落到下一步：

> My recommendation is to use globally consistent datasets for comparison, then add national datasets where they are authoritative. Before modelling, we should agree on the final spatial unit, temporal window, validation approach, and AHP weighting process.

## 3. 如何回应 Mentor 的五个要求

### 数据可用性与适用性

可以这样说：

> I checked the proposed datasets and added real access links where possible. For cross-country comparison, datasets such as CHIRPS v3, SRTM, HydroBASINS, ESA WorldCover, Sentinel-1/2, Landsat, WorldPop, GHSL, OSM, WDPA, GBIF, and flood-event validation datasets are suitable starting points.

需要记住的具体点：

- CHIRPS v3 应该作为主要降雨数据；CHIRPS v2 只适合作为历史兼容选项。
- SRTM 适合作为基础 DEM；Copernicus DEM GLO-30 可以作为对照，但要说明它是 DSM。
- ESA WorldCover 适合做土地覆盖基准，但不能单独用来证明 2020 到 2021 的土地利用变化。
- 秘鲁的采矿数据应优先使用 INGEMMET/GEOCATMIN。
- 津巴布韦的 mining cadastre 是官方来源，但数据可能仍在清理或修正，所以不能单独作为 active mining 的证据。

不要过度承诺：

> I should not say all datasets are already fully ready. I can say the retained public links were opened successfully, but download workflow, licence terms, account access, and GIS data quality still need to be checked.

### GIS 预处理要求

可以这样说：

> The review makes the GIS preprocessing requirements clearer. The main steps are defining study boundaries, harmonizing CRS, clipping all layers, aligning raster grids, harmonizing resolution, conditioning the DEM, deriving hydrological variables, masking clouds, making seasonal composites, calculating distance indicators, and aggregating indicators by sub-basin or hydrographic unit.

重点解释：

> I suggest deriving raster indicators first, then aggregating them to sub-basin or hydrographic units for final comparison. This should be more stable than only using pixel-level AHP results.

最需要 mentor 确认的问题：

> Upper Mzingwane is a catchment, but Arequipa-Moquegua-Tacna is more like an administrative region. We need to decide whether Peru should be analysed by administrative boundary, ANA hydrographic units, or hydrological units clipped by the administrative region.

### AHP-MCDA 框架与权重

可以这样说：

> The AHP-MCDA framework is useful because it can combine multiple criteria into a priority map. But the weights should not be arbitrary. They should come from expert pairwise comparison, pass the consistency-ratio check, and then be tested through sensitivity analysis.

具体做法：

- 保留主要准则：flood hazard、sediment risk、land use/mining disturbance、environmental sensitivity、socioeconomic exposure、mining pressure、rehabilitation potential。
- 在赋权前先区分 hazard、exposure/vulnerability、mining pressure 和 rehabilitation opportunity。
- 做 sensitivity analysis，检查权重变化是否会显著改变最终优先级地图。

简单解释：

> AHP helps organize expert judgement, but it does not remove uncertainty. Therefore, I should report both the selected weights and the sensitivity of the result to different weights.

### 采矿位置与修复潜力

可以这样说：

> I separated official mining rights from observed mining disturbance. A concession or cadastre polygon does not necessarily mean active mining, so it should be checked using satellite imagery, high-resolution visual interpretation, or local expert knowledge.

秘鲁部分：

> For Peru, INGEMMET/GEOCATMIN should be the main official source for mining information.

津巴布韦部分：

> For Zimbabwe, the official mining cadastre and Ministry of Mines sources are useful, but they need validation because the cadastre data may be provisional.

修复潜力部分：

> I suggest separating rehabilitation need from rehabilitation feasibility. Some places may be highly damaged or high-risk, but they may still be difficult to rehabilitate because of slope, remoteness, access, land tenure, legal constraints, or social feasibility.

一句话说明：

> High risk does not always mean high rehabilitation priority. The intervention layer should consider both need and feasibility.

### 建模前还缺什么

可以这样说：

> The remaining gaps are not just missing datasets. They are mainly modelling decisions that need to be fixed before the GIS workflow starts.

高优先级缺口：

1. 最终空间单元：pixel、sub-basin、hydrographic unit，还是行政区与水文单元结合。
2. 时间范围：使用哪些年份或哪些洪水季。
3. 验证数据：历史洪水记录、卫星洪水范围、EM-DAT、Dartmouth、Copernicus EMS、GloFAS、本地报告或专家判断。
4. 采矿验证：官方 cadastre 是否能和遥感识别结果互相验证。
5. AHP 流程：谁来给专家判断、做几轮、consistency ratio 的阈值是什么。
6. 数据访问：哪些数据完全开放，哪些需要账户、许可、申请或人工下载。

## 4. 需要主动提到的技术风险

如果 mentor 追问方法深度，可以提这些点：

- CHIRPS v3 应优先于 CHIRPS v2。
- RUSLE 估计的是 sheet and rill erosion 风险，不等于真实入河泥沙量。
- WorldCover 不能单独用来解释 2020 到 2021 的真实 land-use change。
- Mining concessions 不等于 active mining footprints。
- AHP-MCDA 适合做 relative priority 或 susceptibility map，但不是物理洪水淹没模型。
- Validation 应该在最终权重确定前就设计好。

## 5. 可以问 Mentor 的问题

建议问这些具体问题：

1. For Peru, should the final analysis use administrative regions, ANA hydrographic units, or hydrological sub-basins inside the three regions?
2. Should the final output be a flood susceptibility map, a flood risk map, or an intervention-priority map?
3. Should rehabilitation potential be part of the main risk model, or should it be a second-stage intervention model?
4. If local hydrometric data are limited, which validation evidence would you prefer?
5. Who should provide the AHP pairwise comparisons, and how many expert rounds are realistic?
6. For Zimbabwe mining data, do we have local or institutional sources that can validate the cadastre and satellite interpretation?

## 6. 如果 Mentor 问：这份文档现在 ready 吗？

可以回答：

> It is ready for methodological feedback and data-source review, but I would not treat it as a final modelling protocol yet. The next step is to lock the study units, time window, validation data, and AHP weighting protocol.

中文理解：

> 这份 review 已经适合请 mentor 看方法和数据源，但还不是最终建模规范。下一步要先确定空间单元、时间范围、验证数据和权重流程。

## 7. 如果 Mentor 问：你具体改了什么？

可以回答：

> I prepared a reviewed version that adds official links, suitability notes, preprocessing requirements, methodological cautions, validation options, and unresolved decisions.

中文理解：

> 我做了一份 review 版本，补充了官方链接、适用性说明、GIS 预处理要求、方法风险、验证选项，以及建模前需要确认的问题。

## 8. 如果 Mentor 问：最大的风险是什么？

可以回答：

> The biggest risk is comparability. Zimbabwe is defined as a catchment, while Peru is currently defined more like an administrative region. If the modelling unit is not made consistent, normalization, weighting, and comparison may be biased.

还可以补充：

> Another major risk is mining-data reliability. Official mining rights need to be separated from actual mining disturbance, especially where cadastral data are incomplete or provisional.

中文理解：

> 最大风险不是某一个数据集缺失，而是比较基础是否一致。Zimbabwe 是 catchment，Peru 是 administrative region，如果空间单元不统一，后面的归一化、赋权和比较都会有偏差。另一个风险是采矿数据可靠性，官方采矿权不能直接等同于实际采矿扰动。

## 9. 结束时可以这样说

> My conclusion is that the framework is solid, but the modelling phase should start only after we finalize the spatial unit, temporal window, validation dataset, data-access constraints, and expert-weighting protocol. I would appreciate your guidance on these decisions before I move from data inventory to GIS implementation.

中文理解：

> 我的结论是，整体框架是成立的，但正式进入建模前，需要先确定空间单元、时间范围、验证数据、数据访问限制和专家权重流程。我希望先得到 mentor 对这些关键决策的建议，再进入 GIS 实施阶段。

## 10. 一分钟极简版

如果时间很短，可以这样说：

> I reviewed the inventory and added official dataset links, suitability notes, preprocessing requirements, AHP-MCDA cautions, mining-data caveats, rehabilitation criteria, and validation options. The framework is suitable for mentor review, but before modelling we still need to confirm the modelling unit, time window, validation data, and AHP weighting process. The most important methodological cautions are that mining concessions are not active mining footprints, RUSLE is an erosion-screening method rather than a sediment-delivery model, and AHP weights need expert input plus sensitivity analysis.

中文理解：

> 我已经把数据链接、适用性、GIS 预处理、AHP 权重、采矿数据风险、修复潜力和验证方案补充进去。现在这份 review 可以给 mentor 看，但还不能直接开始建模。建模前最重要的是确定空间单元、时间范围、验证数据和 AHP 权重流程。
