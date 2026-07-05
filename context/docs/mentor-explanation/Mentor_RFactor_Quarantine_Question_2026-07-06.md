# Sediment criterion — can I drop the rainfall-erosivity factor?

For the sediment criterion, I want to stop spending time on the rainfall-
erosivity factor (R) and use only the soil-erosion structure layer (K × LS × C).
Can I do that?

## Why I'm asking

I built the sediment criterion with the standard USLE chain, but the R factor
turned into a methodological dead end. There are two incompatible families of
R formulas in the literature, about 6× apart, and the only independent check I
have (ERA5 hourly rainfall) is a lower bound, not a decision. I do not have a
sub-daily rainfall dataset that would settle it.

Meanwhile I checked whether the choice of R actually changes the priority map.
It does not. The hotspot pattern is governed by slope length and steepness (LS)
and land cover (C), which I have already verified against the primary sources.
Switching between R families only rescales the soil-loss rate (ton/ha/yr); it
does not change which area ranks first. So for the priority-intervention map,
R is not needed.

## What I'm proposing

Use the K × LS × C erosion-structure layer as the sediment criterion. It is
already built, it matches the reference grid, and it does not depend on R.

Drop R from the prototype critical path. Keep the R-factor investigation I
already did on file as a deferred record, not as an open blocker.

## When I would reopen R

Only if you need a quantitative soil-loss rate in ton/ha/yr for the thesis. In
that case I would need either a sub-daily rainfall dataset (rain gauge or GPM
IMERG) in or near the catchment, or a ruling from you on which R convention to
adopt.

## My recommendation

Use K × LS × C for the prototype. Treat R as a thesis-stage refinement, not a
prototype blocker. This is your call.
