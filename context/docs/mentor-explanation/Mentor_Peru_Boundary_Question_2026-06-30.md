# Mentor Message: Peru Boundary Question

Status: ready to send (Teams message + one figure). One decision needed.

## Short Teams Message

Hi Supervisor, I have a question about the Peru side of the project.

I have finished the Zimbabwe prototype, so I have started looking at the Peru side. The issue is
how to define the Peru study area so the two countries can be compared fairly.

Right now "Peru" is defined as the three regions Arequipa, Moquegua, and Tacna. But these are
administrative boundaries, and they mix several different river systems — some flow to the
Pacific, some inland. Zimbabwe is defined as one catchment (~3,700 km²), so if Peru stays as three
administrative regions (~96,000 km²), the two sides are not really comparable.

I checked the HydroBASINS database and there are candidate river basins inside the three regions
in the same size range as the Zimbabwe catchment. So there are three options, and I need your
decision on which one to use:

1. Keep the three administrative regions as-is (largest scope, but mixes river systems).
2. Use one or a few hydrological basins inside the three regions (comparable to Zimbabwe, but
   does not match the administrative regions).
3. A compromise: hydrological basins clipped to the three regions.

My recommendation is option 2 or 3, because it makes the Zimbabwe-Peru comparison defensible. But
this is your call.

Can you let me know which option you prefer? Once I have that, I can start the Peru terrain
processing in parallel with the Zimbabwe side.

I have a map showing the candidate basins if it would help — happy to share it.

## One Figure To Attach

`outputs/peru_boundary_discovery/peru_boundary_discovery.png`

Caption: candidate HydroBASINS river basins (blue outlines) intersecting the Arequipa-Moquegua-
Tacna area (red dashed envelope). This is a discovery map, not an accepted boundary.

## Supporting Detail (Only If The Mentor Asks)

The three options and their trade-offs:

| Option | How Peru is defined | Area | Pros | Cons |
|---|---|---|---|---|
| 1. Administrative regions | Arequipa + Moquegua + Tacna provinces | ~96,000 km² | matches the named study area; policy-relevant | mixes Pacific-slope and highland river systems; not comparable to a single Zimbabwe catchment |
| 2. Hydrological basins | one or a few HydroBASINS units inside the three regions | ~3,000-14,000 km² per unit (Zimbabwe V1 is ~3,700 km²) | scientifically comparable to Zimbabwe; coherent flood regime per unit | does not match the administrative regions |
| 3. Clipped basins | basins intersecting the three regions | depends on clip rule | compromise | most complex to define |

Why this matters: the whole project is a *comparative* flood-risk study. If the two study areas
are defined by different principles (one by river catchment, one by province), the comparison is
biased before any modelling starts.

What I can do immediately after the decision: run the Peru terrain chain (SRTM, slope, hydrology)
in parallel with the Zimbabwe work, using the same workflow. The public datasets are ready; no
new institutional access is needed except the Peru mining cadastre (INGEMMET/GEOCATMIN), which is
publicly accessible.
