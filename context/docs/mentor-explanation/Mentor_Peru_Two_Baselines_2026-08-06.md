# Two Peru baselines after your no-mining change

Supervisor,

I built your no-mining Land Use change two ways so you can pick which one to
carry forward: **(1)** keep the old top-level weights and only swap the Land
Use subgroup, or **(2)** apply your complete weight table from your last
message. The maps are nearly identical, so this is a small decision, but I'd
like your call before I lock it in.

## What I need from you

**Which version should be the main Peru map from here?** Your message said both
"use the weights as here" (the new 0.34 / 0.25 / 0.17 / 0.10 / 0.14) and "you
can also use the same so you don't redo it" (keep the old top weights), so I
made both rather than guess.

## The two versions

I kept the old top weights in one version (FH 0.35, SE 0.25, LU 0.20, ES 0.12,
SV 0.08) and applied your full table in the other (FH 0.34, SE 0.25, LU 0.17,
ES 0.10, SV 0.14). Both drop mining from the score and keep your LC 0.40 / BV
0.35 / BE 0.25 Land Use subgroup. Your full version also uses the new
sub-weights you wrote out (drainage up to 0.40 in Flood, LS up to 0.50 in
Sediment, water/wetland 0.65 in Environmental, and a three-way Socioeconomic
split: road 0.35, settlements+population 0.35, critical infrastructure 0.30).

## What the comparison shows

The two maps agree very strongly. Across the shared 95% of the study area that
both maps can score:

- Rank correlation between the two priority surfaces: **0.99**.
- The highest-priority 20% footprint **overlaps by 85%** (about 479 of 564 km²
  is selected by both maps).
- The mean priority drops slightly, from 0.52 to 0.50, because you shifted
  weight away from Land Use and toward Socioeconomic.

The stability test you described — "the final map is defensible only when
priority zones remain reasonably stable under these sensitivity tests" — is
satisfied. Changing the weights this much moves the high-priority footprint by
only about 15%.

## Two honest caveats on your full version

1. **Critical infrastructure is a proxy.** You asked for road / settlements /
   critical-infrastructure as a three-way split. I have roads and population,
   but I do not have a real inventory of schools, health facilities, bridges,
   or water utilities. I used mapped-building density as a stand-in for the
   critical-infrastructure component and labelled it that way. If you have, or
   can point me to, an infrastructure dataset, I can replace the proxy.

2. **Bare soil and built-up expansion are single-date in the baseline, but I
   checked them against real change evidence.** The BV and BE layers in both
   baselines come from one 2021 land-cover snapshot, so they show where bare
   ground and built/agricultural land *are*, not where they *expanded*. To test
   whether that matters, I downloaded the MapBiomas Peru annual land-cover
   series (1985–2024) and rebuilt BV and BE from real 2015→2024 transitions
   (vegetation loss, built-up expansion, agricultural expansion). Swapping the
   single-date proxies for the real change layers moves the high-priority
   footprint by only 6% — the top-20% overlap between the single-date baseline
   and the real-change version is 0.94. So the single-date proxies are adequate
   for the current provisional map; the real change evidence is preserved as a
   separate test if you want to promote it.

## What I have ready for you

- The two baseline maps and the side-by-side comparison figure and table are
  in `outputs/srtm_1arcsec_peru_pilot/pim_versions/comparison_v02_v07/`.
- The MapBiomas real-change test (single-date BV/BE swapped for 2015→2024
  transitions) is in version 05, with its own comparison against the baseline.

— Jiale
