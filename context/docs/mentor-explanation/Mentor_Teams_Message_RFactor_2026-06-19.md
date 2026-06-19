# Mentor Teams Message: R-Factor

For Microsoft Teams chat. Short, spoken-style. Attach the briefing
`Mentor_RFactor_Investigation_Briefing_2026-06-19.md` and the three boards when sending.

**English** = paste to the mentor. **中文** = your reference.

---

## Send

**EN:**

> Quick one on the rainfall erosivity (R) factor. I found the formula I'd been using was wrong (a break point that isn't in the original paper), so I redid the whole thing.
>
> I tested the standard literature formulas + computed an R directly from ERA5 hourly rainfall as an independent check. Bottom line:
> - The US/Morocco formulas (incl. Elwell's Zimbabwe one) give R ~1400-3700 — about 4x too high for our semi-arid area.
> - ERA5 + the simpler regional equations (Hurni, Epworth/Harare) give R ~250-500, which the ERA5 data supports.
>
> Suggested soil loss A is ~0.6 t/ha/yr with this R (vs ~2-4 if the high formulas were right).
>
> One question: do I use the ERA5-based R (~500) from here on? That's your call. The alternative is I chase a rain-gauge / GPM dataset for a stricter 30-min R. Details + plots in the attached note.

**中文:** 雨强侵蚀力 R 因子跟您说下。我之前用的公式断点不对（原文里没有），整个重做了。
>
> 测了标准文献公式，又用 ERA5 小时降雨直接算了个 R 做独立验证。结论：美国/摩洛哥那套（含 Elwell 的津巴布韦版）给 R ~1400-3700，对我们这种半干旱区偏高约 4 倍；ERA5 加上 Hurni、Epworth（哈拉雷）这类简化公式给 R ~250-500，ERA5 数据也支持这个量级。
>
> 这样算下来土壤流失 A 约 0.6 t/ha/yr（高公式会给 2-4）。
>
> 一个问题：后面用 ERA5 的 R（~500）需要您定一下，还是您希望我找雨量站 / GPM 数据做更严格的 30 分钟 R？细节和图在附件里。

---

## Notes for sending

- Attach: `Mentor_RFactor_Investigation_Briefing_2026-06-19.md` (the full story) and the three
  PNG boards (`mentor_era5_empirical_rfactor_board.png`,
  `mentor_era5_rfactor_raster_board.png`, `mentor_rfactor_exploration_board.png`).
- Keep it to ONE question (ERA5-based R OK, or chase gauge/GPM?). Do not bundle the other R-family
  details into the chat - they are in the attached note if the mentor wants depth.
- If the mentor only reacts to the headline and not the question, default is to proceed with the
  ERA5-based R as an EXPLORATORY label and record the decision as still-open.
