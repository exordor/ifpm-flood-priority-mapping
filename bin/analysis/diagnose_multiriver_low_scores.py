#!/usr/bin/env python3
"""TOOLING: immutable component semantics and normalization diagnostics."""
import json
from pathlib import Path
import numpy as np
import geopandas as gpd
from compare_goslar_multiriver import ROOT,BASE,sha,read_grid,raster_mask,clean_ring,write_csv
OUT=BASE.parent/'component_semantics_v1'
SOURCE=BASE.parent/'multiriver_comparison_v1'
def main():
    OUT.mkdir(parents=True,exist_ok=True);inputs={}
    def read(path,ref=None):inputs[str(path.relative_to(ROOT))]=sha(path);return read_grid(path,ref)
    prior=json.loads((SOURCE/'manifest.json').read_text())
    for rel,h in prior['inputs'].items():assert sha(ROOT/rel)==h,rel
    for f in [BASE/'frozen_normalization.json',Path(__file__).with_name('compare_goslar_multiriver.py')]:inputs[str(f.relative_to(ROOT))]=sha(f)
    m=json.loads((BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    inputs[str((BASE/'chain/priority_scenarios/run_manifest.json').relative_to(ROOT))]=sha(BASE/'chain/priority_scenarios/run_manifest.json')
    pim,ref=read(ROOT/m['priority_raster_lineage']['path']);valid=np.isfinite(pim)
    layers={k:read(ROOT/e['path'],ref)[0] for k,e in m['criterion_raster_lineage'].items()}
    special={'water_wetland_context':'environmental_sensitivity_v0_1/water_wetland_context_0_1.tif','protected_ecological_context':'environmental_sensitivity_v0_1/protected_area_context_0_1.tif','settlement_population':'exposure_indicators/population_exposure_0_1.tif','critical_infrastructure':'exposure_indicators/built_infrastructure_exposure_0_1.tif'}
    components={}
    for ws in m['component_weights'].values():
        for k in ws:components[k]=read(BASE/'chain'/special.get(k,f'criteria_stack/criteria/{k}_0_1.tif'),ref)[0]
    rawpaths={'ls_raw':'chain/ls_factor/goslar_focus_ls_factor_capped50_hillslope_30m.tif','soil_k_raw':'chain/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif','c_raw':'landcover/c_factor_goslar_focus_30m.tif','slope_degrees':'chain/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif','tree_cover_decline_fraction':'landcover/clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif'}
    raw={k:read(BASE/p,ref)[0] for k,p in rawpaths.items()};wc=read(BASE/'landcover/worldcover_aligned.tif',ref)[0]
    anchors=json.loads((BASE/'frozen_normalization.json').read_text());checks=[]
    for k,r,a in [('ls_factor','ls_raw','criteria_stack:2'),('soil_k_factor','soil_k_raw','soilgrids_kfactor:0'),('c_factor','c_raw','criteria_stack:3')]:
        par=anchors[a];s=np.clip((raw[r]-par['clip_low'])/(par['clip_high']-par['clip_low']),0,1);z=valid&np.isfinite(s)&np.isfinite(components[k]);err=float(np.max(abs(s[z]-components[k][z])))
        assert err<1e-5,(k,err)
        assert np.array_equal(np.isfinite(s)&valid,np.isfinite(components[k])&valid),k
        checks.append(dict(component=k,raw=rawpaths[r],anchor_low=par['clip_low'],anchor_high=par['clip_high'],max_error=err,finite_mask_equal=bool(np.array_equal(np.isfinite(s)&valid,np.isfinite(components[k])&valid))))
    geo=SOURCE/'comparison_boundaries.gpkg';inputs[str(geo.relative_to(ROOT))]=sha(geo)
    ps=gpd.read_file(geo,layer='products');ex=gpd.read_file(geo,layer='ring_exclusion').geometry.union_all()
    rows=[];classes=[];effective=[]
    for _,p in ps[ps.family=='regulatory'].iterrows():
        inside=raster_mask(p.geometry,ref)&valid
        if not inside.any():continue
        ring=raster_mask(clean_ring(p.geometry,1000,ex),ref)&~raster_mask(ex,ref)&~inside&valid
        for zone,z in [('inside',inside),('ring',ring)]:
            for family,group in [('criterion',layers),('component',components),('raw',raw)]:
                for k,a in group.items():
                    vals=a[z&np.isfinite(a)];n=len(vals)
                    rows.append(dict(river=p.river,zone=zone,family=family,layer=k,zone_cells=int(z.sum()),valid_cells=n,missing_share=1-n/z.sum(),mean=float(vals.mean()) if n else None,median=float(np.median(vals)) if n else None,p10=float(np.quantile(vals,.1)) if n else None,p90=float(np.quantile(vals,.9)) if n else None,zero_share=float((vals==0).mean()) if n else None))
            for cat in np.unique(wc[z&np.isfinite(wc)]):classes.append(dict(river=p.river,zone=zone,class_code=int(cat),cells=int((z&(wc==cat)).sum()),share=float((wc[z]==cat).mean())))
            for criterion,ws in m['component_weights'].items():
                den=sum(w*np.isfinite(components[k]) for k,w in ws.items())
                rec=np.zeros(pim.shape)
                for k,w in ws.items():
                    ew=np.divide(w*np.isfinite(components[k]),den,out=np.zeros(pim.shape),where=den>0)
                    rec+=np.nan_to_num(components[k])*ew
                    effective.append(dict(river=p.river,zone=zone,criterion=criterion,component=k,nominal_weight=w,mean_effective_weight=float(ew[z].mean())))
                assert np.max(abs(rec[z]-layers[criterion][z]))<1e-5
    write_csv(OUT/'component_statistics.csv',rows);write_csv(OUT/'landcover_composition.csv',classes);write_csv(OUT/'effective_component_weights.csv',effective);write_csv(OUT/'normalization_checks.csv',checks)
    write_note(rows)
    inputs[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    for p,h in inputs.items():assert sha(ROOT/p)==h
    (OUT/'manifest.json').write_text(json.dumps(dict(claim_level='diagnostic_only',command='.venv/bin/python bin/analysis/diagnose_multiriver_low_scores.py',inputs=inputs,model_changed=False,normalization_checks=checks,outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    for r in rows:
        if r['zone']=='inside' and r['family']!='raw':print(r['river'],r['layer'],r['mean'],'missing',round(r['missing_share'],3))
def write_note(rows):
    text='# Semantic diagnosis of low non-flood scores\n\nThe conclusion of this round is that the low erosion and land-use scores broadly follow from the existing inputs and calculation rules, but what these rules measure is not the same as river inundation risk. The environmental criterion is not low; the socioeconomic criterion is limited by what its proxies mean and by population coverage. Replays of the three frozen normalizations passed, and no reversed value direction or calculation inconsistency was found for these three components; this does not prove that the normalization anchors, proxy indicators and input classifications have been validated against reality.\n\nScope: the original 34% model, valid cells inside the official designated extents, and the same cleaned 1 km ring. Model inputs and weights are not modified. Reproduce: `.venv/bin/python bin/analysis/diagnose_multiriver_low_scores.py`.\n\n| River | Erosion factor inside/outside | Land use inside/outside | Environmental inside/outside | Socioeconomic inside/outside |\n|---|---|---|---|---|\n'
    for river in ['Abzucht','Grane','Oker','Innerste']:
        cells=[]
        for k in ['sediment','landuse_asm','environmental','socioeconomic']:
            values=[next(r['mean'] for r in rows if r['river']==river and r['layer']==k and r['zone']==z) for z in ['inside','ring']]
            cells.append('/'.join(f'{v:.3f}' for v in values))
        text+='| '+river+' | '+' | '.join(cells)+' |\n'
    text+='\n## Assessment by criterion\n\n1. Erosion factor: the low scores are explainable in some places, but they do not mean low inundation risk.\nInside the Oker extent the mean slope is 2.91 degrees, versus 10.68 degrees in the outside ring; inside the extent the current WorldCover classes are about 63.8% trees and 29.1% grassland. Low slopes and low C values together produce the low erosion score. Grane also shows gentler slopes inside the extent. The "flatter terrain" explanation cannot be applied to Innerste: in its 12 cells the slope and LS are higher than in the outside ring, and the low composite erosion score is mainly due to the scoring combination, including the low C values of forest/grassland.\nC is assigned from a land-cover lookup table: the raw forest value of 0.001 becomes 0.005 with the 0–0.2 anchors, and grassland 0.02 becomes 0.1; small values match the direction of the current cover-management proxy. The frozen LS anchors are about 0.055–24.779, while the mean valid LS for Oker is 1.269, so the low normalized values can be explained by this scale. K only indicates the position relative to the frozen anchors; an effective resolution of 250 m cannot provide 30 m soil detail.\nThe current sediment criterion is a weighted mean of K, LS and C, not the RUSLE product or an actual sediment yield. The USDA describes RUSLE2 as covering rill/interrill erosion and transport on hillslopes, which cannot directly replace an assessment of river inundation: [USDA ARS](https://www.ars.usda.gov/southeast-area/oxford-ms/national-sedimentation-laboratory/watershed-physical-processes-research/research/rusle2/revised-universal-soil-loss-equation-2-how-rusle2-computes-rill-and-interrill-erosion/).\n\n2. Land use: the low scores match the narrow meaning of the proxies, and some names are inaccurate.\nland_cover_pressure actually uses a runoff-pressure lookup table: trees 0.15, grassland 0.35, cropland 0.70, built-up 1. bare_soil_vegetation_loss is actually the share of positive tree-cover-density decline over 2018–2024; the Oker mean is 0.0052 (about 0.52 percentage points), so a value near 0 does not mean the land surface has no flood risk, nor that there is no bare soil. Stable cropland, grassland and built-up areas do not automatically score high on this component.\nbuilt_agriculture_road_expansion is actually a combination of current built-up/agricultural classes and road proximity; it does not measure expansion and should be called a current development/agriculture and road-proximity proxy. This naming mismatch requires a corrected interpretation, but this round does not change the model code or results. In the direct combination of the three components, the measured magnitude of tree-cover change differs from the other lookup/distance scores; sharing the 0–1 range does not mean their scales of influence are matched. This is a later calibration question, and the values must not be re-stretched merely to raise scores.\n\n3. Environmental criterion: not the main factor lowering the score.\nThe mean environmental score inside the extents of the four rivers is about 0.85–0.96. It comes from proximity to water bodies/wetlands and protected areas, which supports a "close to these features" interpretation; it does not represent full ecological sensitivity.\n\n4. Socioeconomic: Oker and Abzucht are not low, and this result cannot be used to conclude that Innerste is sparsely populated.\nShare of missing population component inside the extents: Grane 69.2%, Abzucht 54.5%, Oker 77.7%, Innerste 100%. Missing population is not zero population. For Innerste the infrastructure-proximity score is about 0.011 and the road-proximity score about 0.985; with the missing population removed, the weights redistributed to the remaining two components produce a socioeconomic score of about 0.535. This only shows that the existing OSM candidate facilities are far away; it does not prove that there are actually few facilities or that social vulnerability is low. The 20 km road decay pushes all road scores inside the extents close to 1, which limits their discriminating power; the existing components also do not measure vulnerability factors such as income or coping capacity.\n\n## Missing components and normalization limits\n\nLS is deliberately set to empty in channel cells with a flow accumulation greater than 500 cells; there are also cases of invalid input, so not all empty LS values can be attributed to this rule. K and population also have insufficient coverage. When a component is missing, the remaining weights are re-averaged, so a missing component may either raise or lower the result; the direction depends on the value the missing component would have had. It cannot be claimed that missing components automatically lower the PIM.\nnormalization_checks.csv checks the formula from raw K/LS/C to the frozen scores, the finite-value masks and the maximum error; effective_component_weights.csv lists the spatially varying effective component weights. The land-cover classification and soil properties have not yet been verified by field survey or independent high-resolution data; this is a consistency check of input, formula and meaning.\n\n## Priority order\n\nFirst align the proxy names with what they actually mean, and keep the low values that can be explained; next clarify whether population gaps mean no coverage or no record, and check the completeness of the OSM facilities; then assess whether tree-cover change and the other 0–1 components have comparable units, and whether the road-decay scale is justified. Only after these questions are settled should new scoring rules be considered. There is currently no evidence to support raising all low non-flood scores across the board.\n'
    (OUT/'READING_NOTE.md').write_text(text)

if __name__=='__main__':main()
