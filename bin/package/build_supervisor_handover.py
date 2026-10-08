#!/usr/bin/env python3
"""TOOLING: prepare a local, private handover snapshot; never upload or send."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
NAME = 'IFPM_Supervisor_Handover_2026-10-08'
DEST = ROOT / 'exports' / NAME
ARCHIVE = DEST.with_suffix('.zip')
EXCLUDED = {
    'data/raw/minedu_censo_educativo_2023_secocha': 'Raw school register includes personal contacts; sanitized output retained.',
    'data/raw/emdat_public_validation_candidate': 'Raw archive restriction; registry is stale about download status.',
    'data/raw/mentor_voi_rainfall_measurements_2026-06-24': 'Private third-party source; not required for current mainline.',
    'outputs/mentor_voi_rainfall_intake': 'Derived private third-party rainfall intake.',
}
SKIP = {'.git', '.venv', '__pycache__', '.pytest_cache', '.ruff_cache', '.DS_Store', 'node_modules'}
SOURCE_DIRS = ['bin', 'tests', 'data/raw', 'data/validation', 'outputs', 'ifpm-flood-pipeline',
               'context/docs/data-management', 'context/docs/research-map', 'context/docs/methodology']
SOURCE_FILES = ['AGENTS.md', 'README.md', 'pyproject.toml', 'uv.lock', 'pipeline.yaml', '.gitignore']
REVIEW_SOURCE = 'exports/IFPM_Goslar_Secocha_Sharing_Package_2026-08-18'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def eligible(path):
    rel = path.relative_to(ROOT)
    if any(p in SKIP for p in rel.parts) or path.is_symlink():
        return False
    if path.name.startswith('.env') or path.suffix in {'.pyc', '.part', '.partial', '.pem', '.key'}:
        return False
    if any(word in path.name.lower() for word in ('credentials', 'cookies', 'token_ifpm')):
        return False
    return not any(rel.as_posix() == p or rel.as_posix().startswith(p + '/') for p in EXCLUDED)


def copy_tree(src, target):
    if not src.is_dir():
        raise FileNotFoundError(f'Required source directory missing: {src}')
    for p in sorted(src.rglob('*')):
        if p.is_file() and eligible(p):
            q = target / p.relative_to(src)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)


def qgis_check():
    checks = []
    for p in (DEST / '01_Review_August_Snapshot').rglob('*.qgz'):
        with zipfile.ZipFile(p) as z:
            xml = ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.qgs'))))
        for node in xml.findall('.//projectlayers/maplayer'):
            provider = node.findtext('provider')
            value = node.findtext('datasource') or ''
            if provider not in {'ogr', 'gdal'}:
                checks.append({'project': str(p.relative_to(DEST)), 'provider': provider, 'status': 'not_local_file_provider'})
                continue
            source = value.split('|')[0]
            resolved = (p.parent / source).resolve()
            ok = resolved.is_relative_to(DEST.resolve()) and resolved.is_file()
            checks.append({'project': str(p.relative_to(DEST)), 'provider': provider, 'status': 'present' if ok else 'missing_or_external', 'source': source})
    if not checks or any(c['status'] == 'missing_or_external' for c in checks):
        raise RuntimeError('Portable QGIS file references failed; see check report.')
    return checks


def main():
    if DEST.exists() or ARCHIVE.exists():
        raise SystemExit('Refusing to overwrite an existing handover snapshot.')
    for name in SOURCE_DIRS + [REVIEW_SOURCE]:
        if not (ROOT / name).is_dir():
            raise FileNotFoundError(f'Required source directory missing: {name}')
    for name in SOURCE_FILES + ['context/docs/mentor-explanation/Supervisor_Handover_Draft_2026-10-08.md',
                                'context/docs/mentor-explanation/Supervisor_Handover_Email_Draft_2026-10-08.md']:
        if not (ROOT / name).is_file():
            raise FileNotFoundError(f'Required source file missing: {name}')
    DEST.mkdir(parents=True)
    workspace = DEST / '02_Research_Workspace'
    workspace.mkdir()
    for name in SOURCE_DIRS:
        print('Copying', name, flush=True)
        copy_tree(ROOT / name, workspace / name)
    for name in SOURCE_FILES:
        shutil.copy2(ROOT / name, workspace / name)
    copy_tree(ROOT / REVIEW_SOURCE, DEST / '01_Review_August_Snapshot')
    shutil.copy2(ROOT / 'context/docs/mentor-explanation/Supervisor_Handover_Draft_2026-10-08.md', DEST / 'HANDOVER_EN.md')
    shutil.copy2(ROOT / 'context/docs/mentor-explanation/Supervisor_Handover_Email_Draft_2026-10-08.md', DEST / 'EMAIL_DRAFT_EN.md')
    (DEST / 'START_HERE.md').write_text('''# IFPM handover to Supervisor — 8 October 2026

My contract has ended. This snapshot preserves my available project work for continuation by Supervisor or the next researcher. Start with HANDOVER_EN.md.

- 01_Review_August_Snapshot: existing presentation, Excel references, diagrams and four portable QGIS review/audit projects, dated 18 August. Open ReviewMap before FullAudit. These are orientation materials, not the September state.
- 02_Research_Workspace: code including currently uncommitted work, tests, data, output history and selected technical provenance. Relative paths are preserved. The independent deliverable scaffold remains in its own subdirectory.
- Latest expanded Goslar comparison: 02_Research_Workspace/outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/ . Its READING_NOTE.md is Chinese; the English handover explains the central result. GeoTIFF and GeoPackage files can be loaded directly in QGIS.
- Other September Abzucht diagnostics and candidate corrections: 02_Research_Workspace/outputs/goslar_abzucht_display_rectangle_v1/ . HQ100-tuned alternatives are sensitivity results, not independent validation.
- Secocha: 02_Research_Workspace/outputs/peru_secocha_a7367_reference_extent_v1/ . This is a provisional map-reference extent, not a catchment.

Private internal handover preparation only. This is not a public release or a blanket clearance of third-party redistribution rights. Source registries retain access/licence conditions; some historical raw inputs have unresolved transfer terms. No files have been uploaded or emailed by the packaging step. Review institutional access conditions before distributing source data beyond the project.

Read EXCLUSIONS.json for the deliberately omitted raw personal-contact register, restricted EM-DAT file, and private rainfall archive. Sanitized project outputs and source notes are retained where applicable. Login material, temporary download directories, virtual environments, Git databases and private mentor-preparation notes are excluded. Excluded source data may need to be obtained by the receiving researcher for historical reruns.

This is an evidence snapshot, not a new model run. Older outputs, deprecated products and working documents are preserved as history and must retain their original status. Some overview/quick-start text predates September and describes obsolete weights or frozen output destinations. Use output-local run manifests for the included results. Do not run into the frozen former Peru output tree. Existing source/manifests may contain historical machine paths; these are provenance, not portable execution instructions. Some old scripts require adaptation on another machine.

Reproduction: recreate the root Python environment from pyproject.toml and uv.lock; the hydrology runners also require WhiteboxTools and its executable. The deliverable subrepository has separate dependencies. QGIS is needed for the review projects. No environment or account credentials are bundled. Clean-machine execution and visual rendering on Supervisor's machine remain unverified. Recorded model-validation reports refer to original runs, not new checks performed during packaging.

MANIFEST.csv records every payload file's size and SHA-256. PACKAGE_VALIDATION.json records the packaging checks. The ZIP is checked by reading every member and its CRC; the adjacent ZIP.sha256 records archive integrity. These verify the snapshot, not the model's scientific validity.

Please confirm that the files are accessible and that the QGIS review projects open. This handover does not promise a post-contract support period.
''', encoding='utf-8')
    (DEST / 'EXCLUSIONS.json').write_text(json.dumps({'classification': 'EXPORT', 'claim_level': 'diagnostic_only', 'omitted_sources': EXCLUDED,
        'other_omissions': ['data/tmp', 'tmp', '.git', '.venv', 'caches', 'private mentor strategy', 'unrelated root PDF/ZIP and presentation scratch files'],
        'transfer_status': 'local_preparation_only'}, indent=2) + '\n')
    checks = qgis_check()
    status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
    (DEST / 'SOURCE_WORKTREE_STATUS.txt').write_text(status)
    validation = {'claim_level': 'diagnostic_only', 'qgis_local_reference_checks': checks,
                  'model_rerun': False, 'recipient_machine_tested': False, 'source_privacy_exclusions_applied': list(EXCLUDED),
                  'archive_integrity': 'See adjacent archive verification JSON for post-write CRC result.'}
    (DEST / 'PACKAGE_VALIDATION.json').write_text(json.dumps(validation, indent=2) + '\n')
    files = sorted(p for p in DEST.rglob('*') if p.is_file())
    print('Hashing', len(files), 'payload files', flush=True)
    with (DEST / 'MANIFEST.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['path', 'bytes', 'sha256'])
        for p in files:
            writer.writerow([p.relative_to(DEST).as_posix(), p.stat().st_size, digest(p)])
    print('Building ZIP', flush=True)
    stored = {'.zip', '.gz', '.tif', '.tiff', '.jp2', '.jpg', '.jpeg', '.png', '.qgz', '.pptx', '.xlsx', '.pdf', '.7z'}
    with zipfile.ZipFile(ARCHIVE, 'w', allowZip64=True, compresslevel=1) as z:
        for p in sorted(p for p in DEST.rglob('*') if p.is_file()):
            z.write(p, NAME + '/' + p.relative_to(DEST).as_posix(), compress_type=zipfile.ZIP_STORED if p.suffix.lower() in stored else zipfile.ZIP_DEFLATED)
    print('Verifying ZIP members', flush=True)
    with zipfile.ZipFile(ARCHIVE) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError('ZIP CRC failure: ' + bad)
        member_count = len(z.infolist())
    sha = digest(ARCHIVE)
    ARCHIVE.with_suffix('.zip.sha256').write_text(sha + '  ' + ARCHIVE.name + '\n')
    ARCHIVE.with_suffix('.verification.json').write_text(json.dumps({'status': 'passed', 'zip_crc_check': 'all_members_passed', 'members': member_count,
        'bytes': ARCHIVE.stat().st_size, 'sha256': sha, 'claim_level': 'diagnostic_only'}, indent=2) + '\n')
    print(json.dumps({'archive': str(ARCHIVE), 'members': member_count, 'bytes': ARCHIVE.stat().st_size}), flush=True)


if __name__ == '__main__':
    main()
