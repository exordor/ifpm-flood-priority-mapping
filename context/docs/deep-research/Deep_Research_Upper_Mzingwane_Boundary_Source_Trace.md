# 津巴布韦 Upper Mzingwane 子流域边界来源追踪报告

## 执行结论

**结论：不能。** 就目前可公开核验的证据而言，**约 2,138 km² 的 Upper Mzingwane 边界并不能从公共证据中被可靠、可复现地重建**。我能确认的是：公开文献中反复出现了 **2,138 km²** 这个面积值，也能看到作者绘制的研究区地图；但我**没有找到**任何公开可下载、可验证、且明确与该 2,138 km² 对应的 **shapefile、GeoJSON、官方图层、出水口定义、坐标、或完整可复现的分水岭划分方法**。相反，公开证据显示至少并存着**三套不同的“Upper Mzingwane”概念**：一套是近年论文中的 **2,138 km² 作者研究盆地**，一套是 HydroBASINS 的 **全球 DEM/Pfafstetter 固定层级子流域**，另一套是 Zimbabwe Geoportal / 早期 ZINWA 水管理体系中的 **官方或半官方“Upper/Lower Mzingwane”管理子流域概念**。这些概念彼此**不能自动视为等价**。citeturn23view0turn33search0turn42view0turn43view0turn53view0

从“最早公开来源”角度看，**我找到的最早公开文献级 2,138 km² 说法，是 Maviza & Ahmed 2020**。该文明确写出 Upper-Mzingwane sub-catchment “covers an area of 2138 km²”，并且说明其影像处理时使用了“study area boundary shapefile”来裁切数据；但论文**没有说明该 shapefile 来自哪里，也没有发布该边界文件**。因此，**2,138 km² 的最早公开“数字来源”与最早公开“几何来源”并不是同一回事**：前者可追到 2020 论文，后者在公开范围内仍然缺失。citeturn23view0turn15view5turn15view6

从“最权威官方几何来源”角度看，**较早且更接近官方的几何线索，其实指向的是另一套更宽泛的 Upper/Lower Mzingwane 管理边界**。Love, Taigbenu & Jonker 2005 的综述图明确写明 **“Base map after ZINWA (2003)”**，并在参考文献中把 **“ZINWA. 2003. National catchment database. Unpublished GIS database, Harare.”** 列为来源；同文还说明在 ZINWA 体制下，Mzingwane catchment 被划分成 **Upper Mzingwane** 与 **Lower Mzingwane** 两个 subcatchments。也就是说，**官方层面的 Upper/Lower Mzingwane 边界很可能确实存在于 ZINWA 未公开 GIS 库中**，但那套边界在公开论文里并**没有被证明等于** 2,138 km² 的作者研究盆地。citeturn51view3turn53view0turn53view1turn53view2

因此，本次追踪的核心判断是：**“2,138 km² 被文献重复”这件事成立；“2,138 km² 的公开可复现几何边界存在”这件事目前不成立。** 如果你的论文要追求方法学可辩护性，最稳妥的做法不是在 HydroBASINS、Zimbabwe Geoportal 和 2,138 文献值之间“择其一默认等价”，而是要把它们**明确区分为三种不同边界概念**，并把最终边界选择建立在**可索取的原始 shapefile / outlet / 官方确认**之上。citeturn33search0turn42view0turn53view0turn23view0

## 证据表

| 来源 | 年份 | 它对 Upper Mzingwane 说了什么 | 是否报告 2,138 km² | 是否提供几何 | 来源类型 | 置信度 |
|---|---:|---|---|---|---|---|
| Görgens & Boroto 见 Love et al. 2005 转述 citeturn51view0turn51view1 | 1997 | 给出的是 **Mzingwane tributary** 的面积与径流贡献：**15,695 km²**、对 Limpopo 的贡献 **9.3%**；不是 2,138 的 Upper Mzingwane 研究盆地。citeturn51view0turn51view1 | 否 | 否 | 早期近原始水文来源，但针对的是更大的 Mzingwane tributary | 高 |
| Love, Taigbenu & Jonker, *An overview of the Mzingwane Catchment, Zimbabwe* citeturn6view0turn51view3turn53view0 | 2005 | 图 1 写明 **“Base map after ZINWA (2003)”**；文中说明 ZINWA 下 Mzingwane 被分成 **Upper** 与 **Lower Mzingwane** 两个 subcatchments；并把 **ZINWA 2003 National catchment database** 列为**未公开 GIS 数据库**。citeturn51view3turn53view0turn53view1 | 否 | **有地图线索，但无公开下载几何** | 近原始综合；对官方管理边界很关键 | 高 |
| Moyce et al., *Alluvial aquifers in the Mzingwane catchment* citeturn52view0 | 2006 | 使用 **Upper Mzingwane / Lower Mzingwane** 的宽泛 catchment 概念，描述上游以商业农业为主、下游主要为 communal lands；研究对象是更大的 Mzingwane catchment 体系。citeturn52view0 | 否 | 否 | 次级，但支持“官方 upper/lower 为宽泛区域” | 中高 |
| Love et al., *Changing hydroclimatic and discharge patterns in the northern Limpopo Basin* citeturn26view0turn27view3 | 2010 | 研究的是 northern Limpopo / Mzingwane 流域站点与径流，不提供 2,138；后续论文常从这类文献借用 Mzingwane climatology。citeturn26view0turn27view3 | 否 | 否 | 次级/背景 | 中 |
| ZINWA National Catchment Database 在公开文献中的存在证据 citeturn53view1turn45search11turn44search9 | 2003 / 2010 | 2005 Love 文献把 **ZINWA 2003** 列为未公开 GIS 数据库；2014/2015 干旱研究图注又把 Mzingwane subcatchments 图来源标成 **ZINWA (2010)**，说明该数据库或其更新版被持续使用。citeturn53view1turn45search11turn44search9 | 未见 | **可能有，但不公开** | 近原始官方但不可访问 | 中高 |
| LBPTC, *Joint Limpopo River Basin Study – Scoping Phase Final Report* 的可见公开线索 citeturn29search1turn41search2 | 2010 | 可见公开摘要只表明 **Zimbabwe 的水需求集中在 Upper Mzingwane River 和 Mwenezi**，Bulawayo 部分位于 Upper Mzingwane River catchment；**我没有在可访问公开片段中找到 2,138 或边界几何**。citeturn29search1turn41search2 | 未见 | 未见 | 可能重要，但本次公开证据不足 | 中 |
| FAO AGRIS：*Bulawayo-Matabeleland-Zambezi: Water supply feasibility study* 记录 citeturn36view0 | 1996 | 这是一个**书目记录**，说明报告共 3 卷、含 maps/graphs/tables，项目走廊主要沿 Zambezi–Bulawayo 线；**没有提供 GIS 边界文件、坐标或可下载几何**。citeturn36view0 | 否 | 否 | 书目级线索，不是几何证据 | 高 |
| Maviza & Ahmed, *Analysis of past and future multi-temporal land use and land cover changes…* DOI: 10.1080/01431161.2020.1731001 citeturn14view0turn23view0turn15view5turn15view6 | 2020 | **最早公开找到**的 2,138 来源；写明 UMS “covers an area of 2138 km²”；还写明处理时用 **study area boundary shapefile** 裁切影像，但**不说明 shapefile 来源，也不发布文件**。citeturn23view0turn15view5turn15view6 | 是 | **否；仅提到曾用 shapefile** | 最早公开 2,138 文献，但几何来源缺失 | 高 |
| Maviza, Grab & Engelbrecht 预印本 / 2022 论文链条 DOI: 10.1007/s00704-022-04040-5 citeturn10view0turn12view0 | 2021 / 2022 | 延续使用 Upper Mzingwane 研究盆地；图 1 明示地图**由作者提供**，并展示边界与 15 km buffer，但**仍无可下载几何**。citeturn12view0 | 是 | 否；只有作者图件 | 次级重复者，但几何仍不公开 | 中高 |
| Chisadza et al., *Detecting land surface water changes…* citeturn20view0turn21view0turn22view0 | 2022 | 再次报告 **2,138 km²**；图 1 显示与 Maviza 系列极相似的研究盆地边界；方法部分详细写了 Landsat/QGIS 流程，但**没有交代边界 shapefile 的来源**。citeturn20view0turn21view0turn22view0 | 是 | 否 | 次级/衍生 | 高 |
| Chisadza et al., *Ecological vulnerability…* DOI: 10.1080/19475705.2023.2190857 citeturn18view0turn19view0turn37view3 | 2023 | 再次写 **approximately 2138 km²**；图 1 图注为 **“Source: Author”**，说明地图是作者产物；文章没有给出公开边界文件或 outlet。citeturn18view0turn19view0turn37view3 | 是 | 否 | 次级/衍生 | 高 |
| Zimbabwe Geoportal `Sub-Catchments` 数据集 citeturn33search0 | 2025 更新 | 存在一个全国 **Sub-Catchments** 数据集，提供 **GeoJSON** 与 **Shapefile** 资源；但页面元数据中 **Source 空白**、未说明该层的制图依据；因此它是**半官方可下载几何**，但**不能自动当作 2,138 的证据**。citeturn33search0 | 页面未述 | **是，但它显然对应另一套概念或至少来源未明** | 半官方平台数据 | 高 |
| HydroBASINS 技术文档 / Pour Points 技术文档 citeturn42view0turn43view0 | 2014 / 2024 | HydroBASINS 是基于 HydroSHEDS/SRTM 的全球分级子流域产品，15 arc-second 分辨率、Pfafstetter 层级；固定层级子流域并不等于地方命名流域。它有官方 pour points 产品，但这是 **HydroBASINS 自己的 outlet 定义**，不是 2,138 文献边界的证据。citeturn42view0turn43view0 | 否 | **是，但属于另一套全球产品几何** | 原始技术文档 | 高 |

## 来源链追踪

这条来源链实际上分成了**两条互相缠绕、但并不等价的链**。

第一条是**“公开文献中的 2,138 km² 研究盆地链”**。我能公开确认的最早节点是 **Maviza & Ahmed 2020**：论文首次明确写出 Upper-Mzingwane sub-catchment 为 **2,138 km²**，并透露研究时使用过一个“boundary shapefile”，但没有说明其来源。随后 **Maviza/Grab/Engelbrecht 2021 预印本—2022 正式论文**延续该边界，并把地图标成作者提供；接着 **Chisadza 2022** 和 **Chisadza et al. 2023** 重复 2,138，并继续使用几乎同型的作者研究区图，却仍未公开边界数据文件。换句话说，**2,138 在公开链条里最先是“论文文本值”，不是“公开数据产品值”**。citeturn23view0turn15view5turn12view0turn20view0turn18view0turn37view3

第二条是**“官方/半官方 Upper–Lower Mzingwane 管理边界链”**。在 **Love et al. 2005** 中，图 1 明确写出底图来自 **ZINWA (2003)**，并明确说明在 ZINWA 体制下 Mzingwane catchment 被分成 **Upper Mzingwane** 与 **Lower Mzingwane** 两个 subcatchments；该文参考文献又把 **ZINWA 2003 National catchment database** 标注为**未公开 GIS 数据库**。更晚一些，2014/2015 的干旱预警研究又把 Mzingwane 的 subcatchments 底图来源标成 **ZINWA (2010)**。这说明：**官方 Upper/Lower Mzingwane 几何大概率长期存在于 ZINWA 国家流域数据库体系中**，但公开文献只暴露了“有这个数据库”，没有暴露可下载几何。citeturn51view3turn53view0turn53view1turn45search11turn44search9

这两条链之所以容易被混淆，是因为后来的 2,138 文献**借用了早期官方 Upper Mzingwane 叙述中的多个属性**。最显眼的是：Maviza 2020 说 UMS “generates approximately **9.3%** of total run-off into the Limpopo River”；而 Love 2005 所转引的 Görgens & Boroto 1997 中，**9.3% 对应的是整个 Mzingwane tributary（15,695 km²）**，不是 2,138 km² 的研究盆地。这个对应关系很像是把“更大官方 Mzingwane 单元”的属性，移植到了“更小作者研究盆地”上。换言之，**公开链条里很可能发生了概念漂移（concept drift）或引用漂移（citation drift）**。citeturn23view0turn51view0

可以把这条来源链简化成下面的图：

```text
公开“2,138 km²”链
Maviza & Ahmed 2020
  ├─ 明确写 2,138 km²
  ├─ 说明用过 boundary shapefile
  └─ 但不交代 shapefile 来源
        ↓
Maviza/Grab/Engelbrecht 2021 预印本 / 2022 论文
  └─ 作者提供地图，继续使用同一研究区概念
        ↓
Chisadza 2022
  └─ 重复 2,138；边界文件来源仍未公开
        ↓
Chisadza et al. 2023
  └─ 重复 2,138；Figure 1 仍为 “Source: Author”

官方/半官方“Upper/Lower 管理边界”链
ZINWA National Catchment Database 2003
  └─ 未公开 GIS 数据库
        ↓
Love et al. 2005
  ├─ 图 1 底图 after ZINWA (2003)
  ├─ Upper / Lower Mzingwane 作为官方管理 subcatchments
  └─ Mzingwane tributary 面积 15,695 km²（after Görgens & Boroto 1997）
        ↓
ZINWA 2010（在后续论文图注中继续出现）
  └─ 说明官方 subcatchment GIS 体系延续存在
        ↓
Zimbabwe Geoportal 2025 Sub-Catchments
  └─ 有可下载 GeoJSON/SHP，但元数据未说明与 2,138 的关系
```

基于这两条链，我对你的五个主问题可以压缩成一句话：**最早公开的 2,138 数值来源是 2020 年作者论文；较早且更官方的“Upper Mzingwane 几何”来源是 ZINWA 未公开 GIS 库；两者目前没有被公开证据证明是同一条边界。**citeturn23view0turn53view0turn33search0

## 三种边界概念为何差异巨大

### 文献中的 2,138 km²

文献里的 **2,138 km²** 更像是一个**作者研究盆地（author-defined study basin）**。证据有三点。第一，最早公开写出 2,138 的 Maviza 2020 只给出数字，没有交代边界来源；第二，它明说使用过边界 shapefile，但不公开；第三，后续 Maviza/Chisadza 系列论文的地图都标成作者提供、作者来源，而不是某个官方数据库图层。也就是说，**2,138 在公开世界里停留在“论文声明 + 作者图件”层面**。citeturn23view0turn15view5turn12view0turn19view0turn37view3

更关键的是，这个 2,138 盆地的描述里混入了早期大尺度 Mzingwane 单元的信息。最典型的是前面提到的 **9.3% runoff**：Love 2005 的 9.3% 明确对应 **15,695 km² 的 Mzingwane tributary**，而 Maviza 2020 却把 9.3% 归到 2,138 的 UMS。再如 **450–650 mm** 的 rainfall range，在 Love 2005 中对应的是“the whole of Upper Mzingwane”这个更宽泛官方 subcatchment 叙述。由此看，**2,138 边界很可能不是从早期官方 Upper/Lower 管理边界直接等值继承而来，而是后期作者另行定义的小研究盆地，同时沿用了上位官方单元的背景描述。**citeturn51view4turn23view0turn51view0

### 你本地 HydroBASINS 的约 3,700 km² 候选

HydroBASINS 的本质不是“地方命名子流域名录”，而是**基于 HydroSHEDS 的全球分级流域（global hierarchical sub-basin product）**。官方技术文档写得很清楚：它是由 **15 arc-second** 分辨率 HydroSHEDS/SRTM 数据，在全球统一规则下建立的 **Pfafstetter** 层级子流域体系；每一级都是固定的层级切分，而不是针对某个地方研究中自定义的 basin name 来做拟合。文档还明确说明，同一级上的子流域面积会因为 tributary/inter-basin 结构而不均一，甚至出现相对“oversized” polygons。citeturn42view0

因此，你的 **HYBAS_ID=1071528840（约 3,700 km²）** 候选与文献 2,138 不一致，并不奇怪。**没有被接受的 outlet / pour point 之前，选中某一个 level-7 polygon，本来就不能证明它等于文献作者的 UMS。** 另外，HydroBASINS 2024 的官方 pour-points 产品虽然能给每个 HydroBASINS sub-basin 一个官方 outlet 点，但那是 **HydroBASINS 自己的子流域 outlet**，不是 Maviza/Chisadza 的 2,138 研究边界 outlet。换句话说，HydroBASINS 可以支持**你自己定义一个可复现的 DEM-based basin**，但它**不能反向证明** 文献里的 2,138 就是哪一个固定 HYBAS polygon。citeturn42view0turn43view0

### Zimbabwe Geoportal 的约 7,321.5 km² Upper Mzingwane

Zimbabwe Geoportal 至少说明了一件重要事实：**公共平台上确实存在一个带“Upper Mzingwane”标签的半官方/官方风格子流域 GIS 数据集体系**。其 `Sub-Catchments` 页面写明资源中有 **GeoJSON** 和 **Shapefile**，但下载需要登录；同时页面元数据里的 **Source 项是空白**，也没有给出制图依据、版本沿革或分水口说明。这意味着它是**可访问到“几何存在”层面**的证据，但不是“几何被充分溯源”层面的证据。citeturn33search0

从面积逻辑和旧文献语义上看，**Geoportal 的 7,321.5 km² 更像官方 Upper/Lower Mzingwane 管理子流域那一套，而不像 2,138 的作者研究盆地**。Love 2005 中，整个 **Mzingwane tributary** 面积是 **15,695 km²**；同文又明确说该 catchment 在 ZINWA 下分成 **Upper** 和 **Lower Mzingwane** 两个 subcatchments。一个大约 **7,300 km²** 的 “Upper Mzingwane” 正好与“15,695 的大单元被分成上下两部分”的逻辑更接近。这个判断是推断，不是直接证实；但它比把 7,321.5 当作 2,138 的同义边界要合理得多。citeturn51view0turn51view3turn33search0

## 对各候选来源的判断

**ZINWA National Catchment Database 2003 / 2010：很可能是官方 Upper/Lower Mzingwane 管理边界的源头，但不是已公开可验证的 2,138 几何源头。** Love 2005 已经把它作为底图基础明确写出，而且 2014/2015 的干旱研究仍把 Mzingwane subcatchments 图源写作 ZINWA (2010)。这说明**数据库存在且被研究者反复使用**。但在公开可得材料里，我没有看到该数据库给出 **2,138 km² 的 Upper Mzingwane study basin**、也没有看到可下载几何。更可能的情况是，它保存的是**官方水管理 Upper/Lower 边界**。citeturn53view0turn53view1turn45search11turn44search9

**Surveyor General Zimbabwe map products：目前没有公开证据显示它们直接提供了 2,138 的 Upper Mzingwane polygon。** 在本次可检索证据中，Surveyor General 更多是作为地质图、植被图或底图数据来源被旁引，而不是 2,138 Upper Mzingwane study basin 的直接边界来源。可追的实物线索反而是 Love 2005 提到的 **Nyabeze (2004a, 2004b) 1:250,000 GIS-based water resources model of the Mzingwane Catchments**；如果这个模型曾使用 Surveyor General 图件，它也更可能是**档案线索**而不是目前公开的 2,138 shapefile。citeturn51view0turn50search3turn50search11

**Bulawayo / Matabeleland / Zambezi feasibility studies：可能与“Upper Mzingwane River catchment 供水规划”有关，但本次没有找到能直接支持 2,138 几何的公共证据。** FAO AGRIS 只给出了书目级记录，说明报告有地图、图表、三卷本，但并未公开 GIS 边界。能够看到的更后期政策摘要只说明 Bulawayo 的供水发展与 Upper Mzingwane River catchment 有关，**并未给出 2,138 的边界可复现信息**。所以这条线索仍值得档案追索，但**目前不能把 feasibility studies 当作 2,138 边界已证实来源**。citeturn36view0turn41search2turn29search1

**Maviza & Ahmed 2020：是 2,138 数值最早公开来源，也是后续论文最可能的直接“文献母本”；但它不是几何可复现来源。** 如果你的问题是“2,138 从哪篇公开论文开始出现”，答案大概率就是这篇；如果问题是“2,138 边界从哪份公开 GIS 来”，答案则是否定的，因为这篇论文没有公开 GIS，只是告诉你它曾经用过一个边界 shapefile。citeturn23view0turn15view5

**Maviza, Grab & Engelbrecht 2022；Chisadza et al. 2023：都是面积重复者（area repeaters），不是几何来源证据。** 这两条线都提供了很像样的作者地图，但地图本身不是 reproducible geometry；除非作者提供原始 vector 数据，否则它们只是**图像级证据**。citeturn12view0turn19view0turn37view3

**LBPTC 2010：就目前公开证据，不能认定它是 2,138 的原始权威来源。** 我确实看到一个 2026 年衍生论文把 **Upper Mzingwane 2,138 km²** 与 **Lower Mzingwane 26,936 km² / Shashe 20,140 km² / Mwenezi 13,786 km²** 一并归到 **LBPTC 2010**；但这是**衍生性陈述**，我没有在本次能访问的 LBPTC 主文本公开片段中找到同样的面积表或边界几何。因此，在论文里把 **LBPTC 2010 直接断言为 2,138 原始来源**，目前证据不足。citeturn50search13turn29search1

## 建议的论文工作流

如果你的目标是做一个**可答辩、可审稿防御（defensible）**的硕士论文流程，那么下一步不应该是继续把 2,138 与 HydroBASINS、Geoportal 互相替代，而应该是**先把边界概念从方法上拆开**。

第一，**向作者索取原始边界文件**。最优先联系对象应是 **Maviza & Ahmed 2020** 以及后续使用同一研究区的作者组，因为公开证据已显示他们手里至少存在一个“study area boundary shapefile”，并且后续地图仍然是作者提供。你的邮件请求应该非常具体：要求 **原始 vector 文件（shp / geojson）**、**CRS**、**边界版本日期**、**用于划定该 basin 的 outlet 坐标**、以及**如果是手工编辑，编辑规则是什么**。这是当前最有希望把 2,138 从“数字”变成“几何”的路径。citeturn15view5turn12view0turn37view3

第二，**向 ZINWA 正式提出数据请求**。请求目标不应只写“Upper Mzingwane boundary”，而应明确区分两件事：一是 **National Catchment Database 2003 / 2010 中 Upper Mzingwane 与 Lower Mzingwane 的官方管理边界图层**；二是 **是否存在一个与学术文献 2,138 km² 对应的、更小 hydrological study basin 边界**。如果 ZINWA 回复只有前者，那恰恰证明文献 2,138 不是官方标准 subcatchment polygon。Love 2005 和后续采用 ZINWA 2010 图件的论文，足以为这个请求提供依据。citeturn53view0turn53view1turn45search11

第三，**追档案而不是追“二手引文”**。最值得追的档案对象有两个：一个是 **Nyabeze 2004a/2004b 的 1:250,000 GIS-based water resources model of the Mzingwane Catchments**，因为它可能保存了官方或半官方的流域矢量；另一个是 **Bulawayo–Matabeleland–Zambezi feasibility study** 的纸本/档案馆版本，因为 AGRIS 明确说它有地图与三卷本结构，只是在线记录本身没有公开几何。你可以把这两条线作为“非公开档案验证步骤”写进论文方法附录。citeturn51view0turn36view0

第四，**把导师决策写进方法学，而不是写进脚注**。如果在论文提交前仍拿不到公开或可授权的 2,138 几何，那么最稳妥的做法是：  
在正文里正式声明，**文献报告的 Upper Mzingwane ≈ 2,138 km² 边界当前无法由公共证据复现**；  
并明确区分你面对的三种候选：**作者研究盆地**、**HydroBASINS DEM 子流域**、**Zimbabwe Geoportal / ZINWA 官方管理子流域**。  
然后由导师确认你论文究竟要回答的是 **“复原文献 study basin”**，还是 **“选择一个可复现替代流域用于后续分析”**。这一步如果不写清楚，后面所有遥感、气候、土地利用、SWAT 或干旱分析都会建立在一个可被审稿人轻易质疑的边界前提上。citeturn23view0turn33search0turn42view0

第五，**只有在前四步失败且导师明确批准时，才允许“临时数字化（provisional digitization）”**。因为作者地图上确实带有经纬网、城镇、水坝和河网，可做**近似 digitization**；但这种做法必须在论文中明确标成 **provisional, non-authoritative, image-derived boundary**，不能伪装成“官方 Upper Mzingwane shapefile”。而且一旦采用这种方案，你的方法部分必须同时公开：用的是哪张图、怎么配准、误差来源是什么、为什么它只是临时替代物。公开证据只支持把这一步当**最后退路**，不支持把它当“真实边界已找到”。citeturn12view0turn19view0turn22view0

## 开放问题与局限

本次追踪的最大局限不是文献数量，而是**几何不可访问性**。我确认了 ZINWA 2003/2010 数据库在公开文献中存在，也确认了 Zimbabwe Geoportal 上存在可下载的 Sub-Catchments 数据集页面，但**二者都没有在公开页面上把“2,138 km² 的 Upper Mzingwane”与具体 geometry 明确绑定**。citeturn53view1turn33search0

第二个局限是，**LBPTC 2010 和 feasibility study 的公开在线片段不足以完成几何溯源**。我能看到这些来源与 Upper Mzingwane 的政策/供水规划关联，但没有找到它们公开暴露 2,138 的边界文件、坐标、或 outlet 定义。citeturn29search1turn36view0

第三个局限是，我没有把任何 ResearchGate 图像**当作正式 geometry**。这些图像最多只能证明“作者心中的边界形状大致长什么样”，不能直接证明“边界可以被严格复现”。这一点与你给出的约束完全一致，也是本报告坚持把“面积重复”和“几何证据”分开的原因。citeturn16view0turn12view0turn19view0

## 参考文献与可访问地址

以下仅列本报告中承重最大的来源。每条文献后给出 DOI；如需网页入口，则用代码格式给出可访问地址，避免把普通网页地址误写成正文链接。

Love, D., Taigbenu, A. E., & Jonker, L. (2005). *An overview of the Mzingwane Catchment, Zimbabwe*. WaterNet Working Paper No. 1. 公开访问页见引用。`URL: https://assets.publishing.service.gov.uk/media/57a08ca1e5274a27b2001305/WP1-Mzingwane.pdf` citeturn6view0turn53view0turn53view1

Love, D., Uhlenbrook, S., Twomlow, S., & van der Zaag, P. (2010). *Changing hydroclimatic and discharge patterns in the northern Limpopo Basin, Zimbabwe*. *Water SA*, 36(3). `URL: https://www.researchgate.net/publication/228669061_Changing_hydroclimatic_and_discharge_patterns_in_the_northern_Limpopo_Basin_Zimbabwe` citeturn26view0

Maviza, A., & Ahmed, F. (2020). *Analysis of past and future multi-temporal land use and land cover changes in the semi-arid Upper-Mzingwane sub-catchment in the Matabeleland South province of Zimbabwe*. *International Journal of Remote Sensing*, 41(14), 5206–5227. `DOI: 10.1080/01431161.2020.1731001` `URL: https://doi.org/10.1080/01431161.2020.1731001` citeturn14view0turn23view0

Maviza, A., Grab, S. W., & Engelbrecht, F. (2022). *Twentieth century precipitation trends in the upper Mzingwane sub-catchment of the northern Limpopo basin, Zimbabwe*. *Theoretical and Applied Climatology*, 149, 309–325. `DOI: 10.1007/s00704-022-04040-5` 公开预印本页见引用。`URL: https://doi.org/10.21203/rs.3.rs-350963/v1` citeturn10view0turn12view0

Chisadza, B., Gwate, O., 等. (2022). *Detecting land surface water changes in the Upper Mzingwane sub-catchment using remotely sensed data*. *AQUA — Water Infrastructure, Ecosystems and Society*, 71(10), 1180–1195. 公开 PDF 页见引用。`URL: https://nru.uncst.go.ug/server/api/core/bitstreams/1810b216-ad33-4b6e-98f7-51f088139614/content` citeturn20view0turn22view0

Chisadza, B., Ncube, F., Macherera, M., Bangira, T., & Gwate, O. (2023). *Spatio-temporal variations in the ecological vulnerability of the Upper Mzingwane sub-catchment of Zimbabwe*. *Geomatics, Natural Hazards and Risk*, 14(1), 2190857. `DOI: 10.1080/19475705.2023.2190857` `URL: https://doi.org/10.1080/19475705.2023.2190857` citeturn18view0turn19view0

Moyce, W., Mangeya, P., Owen, R., & Love, D. (2006). *Alluvial aquifers in the Mzingwane catchment: their distribution, properties, current usage and potential expansion*. *Physics and Chemistry of the Earth*, 31(15–16), 988–994. `DOI: 10.1016/j.pce.2006.08.013` `URL: https://oar.icrisat.org/8036/1/Physics%20and%20Chemistry%20of%20the%20Earth_31_15-16_988%E2%80%93994_2006.pdf` citeturn52view0

HydroSHEDS / HydroBASINS Technical Documentation v1.c (2014). `URL: https://data.hydrosheds.org/file/technical-documentation/HydroBASINS_TechDoc_v1c.pdf` citeturn42view0

HydroBASINS Pour Points Technical Documentation v1.0 (2024). `URL: https://data.hydrosheds.org/file/hydrobasins/pour_point/HydroBASINS_PourPoint_TechDoc_v1.pdf` citeturn43view0

Zimbabwe Geoportal. *Sub-Catchments* dataset page. 页面说明有 `sub-catchment_geojson` 与 `sub-catchment_shp` 资源，但需登录下载；页面元数据未公开 source。`URL: https://zimgeoportal.org.zw/datasets/sub-catchments/` citeturn33search0

FAO AGRIS. *Bulawayo-Matabeleland-Zambezi: Water supply feasibility study*（书目记录）. `URL: https://agris.fao.org/search/en/providers/122524/records/64775dba6dafec353e5131ae` citeturn36view0

ZINWA (2003). *National catchment database*. Unpublished GIS database, Harare. 该条目由 Love et al. 2005 公开参考文献所证实，但数据库本身未公开下载。citeturn53view1turn53view2