# 评估你的 review 是否满足 mentor 要求并完成事实核验

## 核心结论

如果把你的两份材料分开看，结论非常清楚：**原始 inventory 版本还不满足 mentor 的要求；research review 版本已经在内容维度上基本满足 mentor 的要求，但在“可直接进入 modelling”的执行层面仍差最后一轮修订。**原始版本主要是数据清单和少量来源入口，缺少系统化的 *GIS preprocessing*、*AHP-MCDA weighting*、采矿与修复判据、访问限制、验证路径与“还缺什么”的成体系讨论；而 review 版本已经把这些维度逐项展开，并且加入了 *validation*、*additional datasets*、country-specific mining caveats 与流程性建议。fileciteturn0file0 fileciteturn0file1

换句话说，**如果你现在发给 mentor 的是 review 版本，而不是原始 inventory 版本，那么它已经达到了“值得导师审阅并给出方法反馈”的水平。**但如果你的标准是“这份文档已经足够作为 modelling phase 的最终技术规格”，那答案仍然是否定的；你还需要把少数“真实但不够直接 / 已过时 / 需要补充访问条件”的链接纠正掉，并把 study unit、temporal window、validation package 和 data-access constraints 再压实一层。fileciteturn0file1

最重要的一点不是框架错了，而是**框架已经基本正确，问题集中在若干高负载项的事实细节**：例如 CHIRPS 现在应优先转向 v3，WorldCover 不能被直接当作 2020–2021 纯净变化检测数据，SoilGrids 的 REST API 目前暂停，Sentinel 的旧 Open Access Hub 早已退役，Peru 的 E-Catastro 页面带有明显 legacy 痕迹，而 Zimbabwe cadastre 官方页面明确提示数据仍在清洗、属于 provisional。citeturn33view0turn5view2turn36view0turn6view0turn13view1turn17view0

## 逐项对照 mentor 要求

**关于数据可用性与适用性。**你的 review 已经不再只是列数据名，而是按 *study area*, *flood hazard*, *sediment risk*, *LULC/ASM*, *environmental sensitivity*, *socioeconomic exposure*, *mining*, *rehabilitation* 和 *validation* 做了来源、适用性与注意事项说明。从“有没有覆盖到 mentor 想看的维度”这个角度，它是满足的。fileciteturn0file1

**关于“add the real links to the data set on the document”。**这一项目前只能评为“**基本满足，但还没有完全做透**”。原因不是你没加链接，而是有些链接虽然真实，却仍停留在 *portal / landing page / legacy page / institution homepage* 层面，而不是“最可执行的官方数据入口”。这在导师视角里通常会被视为“还差一步”，尤其当他打算直接点进去复核时。fileciteturn0file1 citeturn33view0turn36view0turn13view1turn16view0turn27view0

**关于 GIS preprocessing requirements。**这一项你的 review 写得已经明显超过一般“数据清单”水平。你给出了 *clip, CRS harmonization, raster resolution harmonization, DEM conditioning, flood metrics derivation, cloud masking, compositing, zonal statistics, distance-based indicators* 等具体处理建议，这正是 mentor 通常想看到的“你不仅知道用什么数据，也知道数据要怎么进模型”。fileciteturn0file1

**关于 AHP-MCDA framework and weighting approach。**这一项也已经达到“可以讨论”的程度。你不仅写了 Saaty 标度和 *consistency ratio*，还把 *sensitivity analysis*、*expert pairwise comparison* 和“不要只依赖一个 weight set”写进去了；再加上你提出把 *Risk model* 和 *Intervention model* 分两阶段处理，这比原始单一加权和模型更稳健。fileciteturn0file1

**关于 mining location 与 rehabilitation potential criteria。**这一项基本满足，而且是 review 中比较强的一部分。你已经把 Peru 和 Zimbabwe 的 mining data strategy 区分开，把 *concession/rights* 与 *observed disturbance* 分开，又把 *rehabilitation need* 和 *feasibility* 分开，这些都是导师通常会关心的“方法意识”。fileciteturn0file1

**关于 gaps / additional datasets / validation approaches。**这一项也已经满足，因为你不仅列了缺口，还列了验证来源，包括 *EM-DAT*, *Dartmouth Flood Observatory*, *Copernicus EMS*, *JRC Global Surface Water*、local reports 和专家/社区验证思路。你真正还需要补的，不是“有没有想到验证”，而是把验证数据集和时段具体化。fileciteturn0file1

综合来看，这份 review 的状态可以概括为：**内容覆盖上通过，事实与执行细节上待修。**fileciteturn0file1

## 数据与链接事实核验

以下核验基于我对你文档中关键官方来源的直接检查，时间点为 **2026-06-02**。

### 已核验为可靠且适合保留的核心数据源

**HydroBASINS / HydroRIVERS** 作为跨国可比的水文骨架是可靠的。HydroBASINS 官方明确说明它提供全球、层级嵌套的 *sub-basin boundaries*，并采用 Pfafstetter 编码支持上下游拓扑分析；HydroRIVERS 官方则明确说明它提供全球河网、河阶、长度和长期平均流量等属性，而且与 HydroBASINS 共享 ID，便于 basin-based / sub-basin-based aggregation。你的 review 把它们放在 study-area delineation 和 hydrology preprocessing 的核心位置，这个判断是正确的。citeturn2view2turn3view0

**SRTM** 仍然是可接受的基础 DEM。USGS 官方写明 SRTM 1 Arc-Second Global 提供全球 30 m 级高程数据，并说明其世界范围开放分发；对于 Zimbabwe 和 Peru 这两个研究区，都在其覆盖范围之内。把它作为基础 DEM 没问题。citeturn4view0

**ERA5-Land** 的链接与基本描述是正确的。Copernicus Climate Data Store 仍提供该数据集，官方说明其空间分辨率是 0.1° 网格、原生约 9 km，时间覆盖从 1950 年到现在，小时尺度更新。你的 review 把它定位成极端降雨诊断和 hydro-climatic consistency 的辅助数据，而不是当地站点替代品，这个定位是合理的。citeturn2view1

**JRC Global Surface Water** 的可用性和开放性已核实。JRC 数据目录明确写明该数据集可匿名直接访问，*Access conditions* 为 *No limitations*，并提供官方数据访问入口。把它用于 surface water occurrence、seasonality 和湿地/河流敏感性分析是站得住脚的。citeturn8view0

**WDPA / Protected Planet** 的可用性也已核实。Protected Planet 官方页面说明 WDPA 仍是全球保护地数据库，且按月更新、可下载。你把它作为环境敏感性核心图层使用是合适的。citeturn7view2turn7view3

**WorldPop 与 GHSL** 都是当前可用的、可以互补的暴露数据来源。WorldPop Hub 仍在运行，并明确标示开放人口数据与 API/Repository 生态；其主站也说明不同人口产品适用于不同任务，尤其要区分单国近期估计与全球一致性时间序列。GHSL 则继续提供下载向导和直接下载页面，并公开多时相 *GHS-POP*、*GHS-BUILT* 与 10 m / 100 m / 1 km 级建成区产品。你的 review 把 GHSL 作为 WorldPop 的 built-up cross-check，这是一个加分项。citeturn9view0turn32view2turn38view0turn38view1

**EM-DAT、Dartmouth Flood Observatory 和 Copernicus EMS** 的验证价值也被核实。EM-DAT 官方文档说明公共数据对非商业用途在注册后可免费访问，且 Archive 版更适合可复现研究；Dartmouth 页面说明其大洪水档案提供 HTML、Excel/XML 和 GIS shapefile；Copernicus EMS 的 *Access to Data* 页面明确 GloFAS 和 GFM 数据可免费下载。这意味着你 review 里提出的 validation 路线不是空想，而是有真实数据入口支撑的。citeturn19view0turn19view1turn19view3

**HydroATLAS** 是你文档里还可以进一步抬高质量的一项补充。官方说明 HydroATLAS 为 HydroBASINS / HydroRIVERS / HydroLAKES 提供 56 个 hydro-environmental variables、281 个属性，覆盖 hydrology、climate、land cover、soils、anthropogenic influences 等类别。如果你后续希望减少手工拼接多个全球属性图层的工作量，它非常值得加入。citeturn34view0

### 需要修正、替换或加注释的关键项

**CHIRPS 应从 v2 升级为 v3，至少要在文档里解释清楚为什么仍保留 v2。**UCSB 官方已经明确宣布 CHIRPS v3 可用，且 CHIRPS v2 的生产将在 **2026 年 12 月之后结束**；同时 v3 是当前官方主线版本，覆盖更广、并对高强度降雨和时序方差做了改进。你的 review 仍然把 CHIRPS v2 放在中心位置，这在 2026 年已经显得偏旧。更稳妥的做法是：正文主引用 CHIRPS v3，把 v2 作为“与既有研究对齐时可保留的历史版本”来说明。citeturn2view0turn33view0

**ESA WorldCover 可以保留，但绝不能把 2020 与 2021 的差值直接解释为真实 land-use change。**官方页面明确写明 2020 与 2021 地图是由不同算法版本生成的，因此两年差异同时包含真实地表变化和算法差异。这一点对你的 *ASM expansion*、*land-use change* 指标非常关键。也就是说，WorldCover 适合作为 baseline / mask / class prior，但不适合单独承担变化检测主证据；变化检测应以 Sentinel-2 / Landsat 时序为主。citeturn5view2

**SoilGrids 数据本身可用，但不能把 REST API 当成稳健生产链路。**ISRIC 官方面向 2026-01-27 的文档写得很清楚：REST API 目前暂停，且它本来就处于 beta 状态；更稳定的访问方式是 WCS、WebDAV 或新的 web platform。你的 review 已经意识到这一点，但还应该在最终文档中把“推荐访问路线”写死，而不是继续给人一种 API 是默认入口的印象。citeturn5view0turn36view0

**Sentinel 数据访问部分需要去掉“旧链路仍是主入口”的模糊感。**ESA 官方数据访问页面已经明确说明：旧的 *Copernicus Open Access Hub* 自 **2023 年 7 月起逐步退役，并在 2023 年 10 月底停止运行**；当前主分发平台是 *Copernicus Data Space Ecosystem*。因此，你文档里应该把 *Copernicus Browser / API / CDSE* 放在主位，把旧 Hub 只作为历史说明或者干脆删掉。citeturn6view0

**“ALOS PALSAR DEM (12.5 m)” 这个表述需要彻底纠正。**ASF 官方页面是 *ALOS PALSAR Products* 说明页，核心是 SAR Level 1.x 与 terrain-corrected products；12.5 m 在这里对应的是 terrain-corrected SAR 产品分辨率，而不是一个清晰、独立、通用的 DEM 产品入口。你的原始 inventory 把它写成 DEM 是不严谨的。若你只是想要一个统一的 elevation source，**Copernicus DEM GLO-30** 或 **SRTM 1 Arc-Second Global** 会更清楚；并且 Copernicus DEM 官方明确说明它是 **DSM**，包含建筑和植被的顶反射面，这一点要在 hydrologic preprocessing 里说明。fileciteturn0file0 citeturn26view1turn25view0turn4view0

**Peru 的 mining 链接应优先 GEOCATMIN，而不是把 E-Catastro 放在同等主位。**GEOCATMIN 是当前官方 Web GIS 入口；相反，E-Catastro 页面仍写着需要 Netscape / Internet Explorer 插件，这明显带有 legacy 系统特征。把它保留为“历史或备用入口”可以，但不应作为主要数据入口写给 mentor。citeturn13view0turn13view1

**Peru 的 ANA 部分也建议换成更直接的 hydrographic units 下载页。**你 review 里给了一个 ANA geoportal 新闻页和一个 hydrographic units 页面。后者更有价值，因为官方页面明确提供 JPEG 与 shapefile 下载入口；如果 mentor 点进去，这个页面更像“真实数据源”，而不是机构新闻。citeturn16view0

**Zimbabwe mining cadastre 可以用，但必须显式写上“官方仍在清洗，数据属 provisional”。**这一点不是推测，而是 portal 首页直接写出来的。你的 review 已经捕捉到了这一风险，这部分判断是准确的；但建议在最终文档里把这句话前置到 dataset table，而不是只放在正文叙述。citeturn17view0turn17view1

**Zimbabwe 的气象链接目前更像机构和工具入口，而不是“历史观测数据的直接下载链接”。**MSD 官方站点现在提供 *MapViewer*、*Stations*、bulletins 和多类 products，但在我核验的页面上没有看到与 SENAMHI 那样明确的 nationwide historical download endpoint。相比之下，Peru 的 SENAMHI 明确提供全国 meteorological download 页面，并挂有 IDF 相关工具。这意味着两国的 local validation data access 难度并不对称，你应把这一点写进 access constraints。citeturn27view0turn26view2

**GBIF、GloREDa、KBA 和 EM-DAT 都不是“点开即拿到完整数据”的零门槛源。**GBIF occurrence download 需要注册并异步生成下载；GloREDa 官方页面明确写着 *Registration is requested*；KBA GIS 数据对非商业用途也需要申请，而且通常要 **5–10 个工作日**；EM-DAT 公共数据同样需要注册。你的 review 已经部分提到这些限制，但最好把“是否需账号、是否需申请、是否异步、是否有等待时间”加成 inventory 表中的独立字段。citeturn8view1turn5view1turn30view0turn19view0

## 方法与指标体系核验

从方法角度看，你的 review **最有价值的进步**是把原始单层 *Priority Intervention Model* 的思路，重构成了更清楚的两阶段体系：先做 *Risk model*，再做 *Intervention / Feasibility model*。这比把 *hazard*、*vulnerability*、*mining* 和 *rehabilitation opportunity* 直接硬塞进一个加权和更稳健，因为 flood risk 的概念框架本来就强调 *hazard*、*exposure*、*vulnerability / susceptibility* 与 *resilience* 之间的区分，而不是把“好不好修复”直接当成“高不高风险”。fileciteturn0file1 citeturn37academia0

你在 review 中加入 *sensitivity analysis*，这一点不是锦上添花，而是必需项。已有 AHP flood-risk 研究表明，*pixel-based AHP* 对 judgement matrix 的定义非常敏感，而基于 *sub-watershed* 的聚合方法通常更稳定；这恰好支持了你 review 里提出的“尽量以 sub-basin / zonal statistics 作为最终优先级单元”的方向。换言之，mentor 如果认真看方法部分，最可能追问的不是“为什么用 AHP”，而是“你的专家矩阵从哪里来、做几轮、如何做 sensitivity envelope、最终报告哪一组权重”。fileciteturn0file1 citeturn23academia3turn37academia2

关于 *consistency ratio*，你沿用了常见的 **CR < 0.10** 规则，这在 AHP 应用里是标准写法，没有事实性错误。问题不在阈值本身，而在于**文档还没有把执行流程写成可复现协议**：例如谁提供 pairwise comparisons、专家样本量、是否分国家专家与跨国专家、如何合成 group judgment、如何对不同 study area 保持同一套 top-level hierarchy。把这些再补一页，AHP 部分就会从“方法框架”进化为“可执行 technical protocol”。fileciteturn0file1 citeturn39academia2

你的 *sediment risk* 部分总体合理，但有一处最好明确写给 mentor：**RUSLE 估的是 sheet and rill erosion，不等于实际入河输沙量。**FAO 对 RUSLE 的说明很清楚，它用于基于 R、K、LS、C、P 的土壤流失估计，适用于 cropland、construction sites、mined land 等场景；这很适合做 screening 和 relative risk ranking，但如果你的目标是“河道泥沙负荷”或“尾矿对河网的传输影响”，就还需要一个 *sediment delivery / connectivity* 代理层。你的 review 已经意识到这一点，这个判断是正确的。fileciteturn0file1 citeturn40view0

还要特别指出一个跨国比较上的方法风险：**Upper Mzingwane 是水文 catchment，而 Arequipa–Moquegua–Tacna 在你文档里更像 administrative region。**如果不先统一 modelling unit，那么后面的 normalization、aggregation、weighting 与 final comparison 都会掺入单位定义偏差。你的 review 已经把这件事识别出来，这一点非常关键，也说明你已经接近 mentor 想看到的思路深度。fileciteturn0file1 citeturn2view2turn16view0

## 建模前必须完成的修订

在进入 modelling phase 之前，我认为你至少还要完成以下几件事。

**第一，更新 precipitation 主数据源表述。**把 CHIRPS 的主引用切换到 **CHIRPS v3**，并把 v2 改成“历史兼容版本”或干脆移到附注；同时保留 ERA5-Land 作为极端降雨和再分析对照，而不是主降雨源。citeturn33view0turn2view1

**第二，把数据清单改造成真正的 dataset register。**每条数据至少加上 *official landing/download entry*、*access condition*、*login needed*、*license*、*temporal coverage*、*native resolution*、*study-specific role*、*cross-country comparability*。你已经有大部分内容，但现在还是散在正文里，不够让 mentor 一眼判断“是否 ready”。fileciteturn0file1 citeturn36view0turn19view0turn30view0

**第三，替换或降级几个高风险链接。**我建议把 SoilGrids API 改为 WCS/WebDAV 访问说明；把 Sentinel 主入口改成 CDSE；把 Peru 的 E-Catastro 降级为备用；把 ANA 新闻页替换为 shapefile 下载页；把“ALOS PALSAR DEM”改写为更准确的 elevation source 描述。citeturn36view0turn6view0turn13view1turn16view0turn26view1

**第四，锁定 modelling target、modelling unit 和 temporal window。**你现在的 review 已经指出了方向，但还没有最终拍板：到底是 *flood susceptibility*、*flood risk* 还是 *intervention priority*；最终 map unit 是 pixel、sub-basin 还是 clipped administrative hydrological unit；时间窗是近十年、近二十年还是以某个 benchmark flood season 为主。这个决定必须在建模前完成。fileciteturn0file1

**第五，预先组装 validation package。**至少应提前准备好：EM-DAT Archive / Public Data、Dartmouth flood archive shapefiles、Copernicus EMS 的 GloFAS / GFM、JRC Global Surface Water、以及尽可能取得的当地雨量 / 水文记录。对于 event-based flood validation，建议再加入 Sentinel-1 SAR flood extent，因为光学数据会受云影响。citeturn19view0turn19view1turn19view3turn8view0turn6view0

**第六，把 mining 与 rehabilitation 两部分各自再补一页 protocol。**前者要写清楚如何把 *concessions*、*observed disturbance*、*tailings/spoil*、*riparian buffers* 分开；后者要写清楚如何把 *need* 与 *feasibility* 分开，以及如何处理 land tenure、concession status、protected-area restrictions 和 community access。Zimbabwe 的官方 cadastre 已明确提示数据仍是 provisional，而 Peru 的官方矿业入口中也存在 legacy 页面，因此“人工核查 + 遥感验证”不是可选项，而是必要条件。fileciteturn0file1 citeturn17view0turn13view1

最终判断可以概括成一句话：**你的 review 已经达到“可以发给 mentor 审阅”的标准，但还没有达到“无需再改就能启动 modelling”的标准。**最稳妥的做法是：**发送 review 版本，而不是原始 inventory 版本；同时在发送前先完成上述高优先级修订。**这样做之后，这份文档就会从“不错的 research review”升级为“技术上经得起追问的 modelling pre-spec”。fileciteturn0file0 fileciteturn0file1