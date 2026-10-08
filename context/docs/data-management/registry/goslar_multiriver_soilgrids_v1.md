# LOCAL_DATA: expanded Goslar multi-river SoilGrids window

Source: https://files.isric.org/soilgrids/latest/data (SoilGrids 250m mean clay/silt/sand/SOC, 0–5/5–15/15–30cm). Access2026-09-14; same family and Williams K method as baseline. Public ISRIC data, CC-BY4.0; no account. Area9.79,51.76,10.70,52.31, extended flood comparison extent. Expected small cropped250m windows, not global download. Reusable pinned local snapshot; versionlatest pinned by per-file hash.

Destination: data/raw/soilgrids_250m_goslar_multiriver_v1. Command: `.venv/bin/python bin/acquire/pull_goslar_soilgrids_window.py --extent 9.79 51.76 10.70 52.31 --out-dir data/raw/soilgrids_250m_goslar_multiriver_v1`. Original source unchanged. Tool emits file checksums/size/shape and K diagnostics in destination on success. Failed attempts remain identified by absent final diagnostics. Intended use: diagnostic model expansion, not observed flood validation.

Completed: 12 property/depth windows and derived 0–30cm K, shape243×330; 72,621 valid native cells. Derived K SHA256 `f4df49add7a8cebd23131df8daddf3db06d83d257108db8b560b8f258eb04e08`. Individual window hashes and diagnostics are in the destination metadata.
