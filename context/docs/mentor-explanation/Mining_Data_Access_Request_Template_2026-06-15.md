# Mining Data Access Request Template

Date: 2026-06-15

Status: internal mentor-facing request template. This is a drafting aid for the HiWi to adapt when
the mentor confirms they are willing to approach mining/ASM data holders. It is not a request to
be sent verbatim, and it does not authorize any data transfer. Fill the bracketed placeholders
before sending. Keep all access details, contacts, and private links out of committed files.

## Purpose

A short, reusable request frame for approaching Zimbabwe mining/ASM data holders (or equivalent
Peru holders later). The goal is to obtain, at minimum, a small defensible mining-evidence sample
for the V1 working catchment, without overcommitting the project to data the mentor has not
approved.

## Use Rules

- Adapt the wording to the specific institution and the mentor's preferred introduction style.
- Do not name dataset ids, file sizes, or local paths in the outward-facing request unless the
  data holder asks.
- Record the actual contact, access decision, and licence terms in an internal note under
  `context/docs/data-management/registry/` after any positive response. Never commit private
  contact details or access credentials.
- Treat any received data as `LOCAL_DATA` under `data/raw/<dataset_id>/` only, with a registry
  and preflight note, before processing.

## English Draft (Zimbabwe Institutions)

Subject: Request for ASM and mining-evidence data for Upper Mzingwane flood-prioritization study

Dear [contact name / title],

I am a research assistant working with [mentor name and affiliation] on a flood and sediment
prioritization model for the Upper Mzingwane / Matabeleland South area. The study combines
terrain, rainfall, land use, and environmental layers in a multi-criteria framework, and we would
like the mining component to reflect real ASM and mining activity rather than generic indirect indicators.

To support this, may I request, subject to your data-sharing terms:

- ASM site locations or registration points within or near the Upper Mzingwane catchment;
- mining concession or lease boundaries, with any status field that distinguishes active from
  inactive operations;
- any environmental-impact or rehabilitation records EMA or your office holds for the area;
- any guidance on how your office prefers such data to be cited, attributed, or restricted.

We would use the data solely for academic flood- and sediment-priority modelling under
[mentor affiliation]'s supervision, store it on local secure storage, and not redistribute it
without your written permission. I am happy to share the resulting methodology and to acknowledge
your data contribution in any publication.

If a formal application form or institutional letter is required, please let me know and I will
prepare it through [mentor name].

Thank you for considering this request.

[HiWi name]
[affiliation]
[mentor contact, if appropriate to share]

## Chinese Draft (For Internal Mentor Discussion)

The HiWi may use the following frame when discussing the data ask with the mentor before any
outward contact:

> 项目当前的采矿证据层只有 2 个 OSM quarry 多边形，不足以支撑方法学中的 Mining Location 和
> Rehabilitation 两个准则。要补齐这一层，最理想的是通过您或相关机构获取：Matabeleland South 区域
> 的 ASM 站点、矿权边界（含活跃/非活跃状态）、EMA 修复记录，以及引用与使用条款。所有数据将仅在
> 本地安全存储用于学术建模，不会未经许可再分发。如果需要正式申请函或机构介绍信，我可以准备。
> 如果完全无法获取官方采矿数据，是否接受把采矿与修复两个准则降级为定性背景证据？

## Information To Record Internally After Any Positive Response

When a data holder agrees, create a registry note under
`context/docs/data-management/registry/<dataset_id>.md` capturing:

- dataset id and short name;
- source organization and contact role (not private contact details in committed files);
- product/version and access date;
- licence or terms (quote the relevant clause);
- intended destination under `data/raw/<dataset_id>/`;
- expected file types and approximate size;
- whether redistribution is allowed;
- the mentor approval that authorized the access.

Then complete the preflight checklist under
`context/docs/data-management/preflight/<dataset_id>.md` before any actual data transfer.

## Boundaries

- This template does not authorize any outward contact. Send only after the mentor agrees to the
  approach.
- Do not promise data redistribution, public release, or commercial use.
- Do not commit received data, private contact details, or access credentials to Git.
- Received mining data does not auto-enter AHP scoring; it requires the IFPM-D05 mining-data
  interpretation rule and a preflight closure first.

## Cross-References

- Source package: `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_mining_data_decision_package_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (IFPM-D05).
- Templates: `dataset_registry_template.md`, `download_preflight_checklist.md`.
