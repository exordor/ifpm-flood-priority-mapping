# AHP Elicitation Protocol And Template

Date: 2026-06-15

Status: internal mentor-facing instrument for the P1 R1.3 AHP weighting decision. This file
contains the elicitation procedure, a blank pairwise-comparison template, and an explicitly
NON-AUTHORITATIVE illustrative structural prior. Nothing here authorizes a real-data AHP
overlay or any interpretable priority map.

Do not copy the illustrative prior into `ifpm-flood-pipeline/configs/`. It is not a project
matrix. It exists only to give the expert a concrete starting point to react to.

## 1. Saaty 1-9 Scale Reference

| Intensity | Definition | Explanation |
|---:|---|---|
| 1 | Equal importance | Two criteria contribute equally to the objective. |
| 2 | Between equal and moderate | Compromise judgement. |
| 3 | Moderate importance | Experience and judgement slightly favour one over the other. |
| 4 | Between moderate and strong | Compromise judgement. |
| 5 | Strong importance | Experience and judgement strongly favour one over the other. |
| 6 | Between strong and very strong | Compromise judgement. |
| 7 | Very strong importance | A criterion is favoured very strongly; dominance demonstrated in practice. |
| 8 | Between very strong and extreme | Compromise judgement. |
| 9 | Extreme importance | Evidence favouring one over the other is of the highest possible order. |

Reciprocals (1/2, 1/3, ..., 1/9) encode the inverse judgement. The matrix must be reciprocal:
`a_ij * a_ji = 1` and the diagonal is `1`.

## 2. Criteria Hierarchy (To Be Confirmed Before Elicitation)

The default 7-criteria PIM hierarchy from the original methodology:

1. Flood Hazard
2. Sediment Risk
3. Land Use / ASM Pressure
4. Environmental Sensitivity
5. Socioeconomic Vulnerability
6. Mining Location & Intensity
7. Rehabilitation Potential

Prerequisite check before elicitation:

- [ ] Mentor confirms this hierarchy, OR records a revised hierarchy.
- [ ] If the R1.2 mining-data decision falls back to a reduced criteria set (Mining and
      Rehabilitation demoted to context), the hierarchy MUST be revised before elicitation, and
      the blank template below MUST be regenerated for the revised criteria set.
- [ ] Each criterion has an agreed data source and standardization direction (higher-better vs
      lower-better) recorded.

## 3. Elicitation Procedure

### 3.1 Single-expert path

1. Share this file and the V1 evidence board with the expert.
2. Expert fills only the upper triangle of the blank template (Section 4). Lower triangle is
   reciprocal.
3. HiWi enters the values into a CSV matching the pipeline format and runs:
   `uv run ifpm-flood-pipeline ahp --matrix <filled.csv> --consistency-threshold 0.1`
4. If CR <= 0.1, the matrix is accepted. If CR > 0.1, return the matrix to the expert with the
   most inconsistent pairs flagged (the pipeline reports lambda_max and CR; manually inspect
   pairs where the implied ratio diverges most from the stated value).
5. Record the accepted matrix, CR, and date in a registry note. This matrix becomes the only
   authorised project matrix.

### 3.2 Group-expert path (preferred when multiple experts)

1. Each expert fills the upper triangle independently, without consultation.
2. Aggregate using the geometric mean of individual judgements per cell:
   `a_ij_group = (prod_k a_ij_k)^(1/K)` where K is the number of experts.
3. Run the aggregated matrix through the `ahp` command for CR.
4. Additionally run each individual matrix through the `ahp` command and record the
   weight-spread across experts. This feeds the sensitivity analysis (section 3.4).
5. Record all individual matrices, the aggregated matrix, CR values, and the expert roles (not
   private identities in committed files) in a registry note.

### 3.3 Consistency review

- Default CR threshold: 0.1 (configurable via `--consistency-threshold`).
- If the mentor specifies a stricter threshold (e.g. 0.08), use it.
- Any waiver (accepting CR > threshold) must be documented with reason and reviewer approval.
- The `run` command enforces the threshold unless `--allow-inconsistent` is passed; do not pass
  that flag for any interpretable real-data run.

### 3.4 Sensitivity analysis

After an accepted matrix exists, run at minimum:

- +/-20% perturbation on each weight, one at a time; report whether V1 priority-class ranks
  reverse for any perturbation.
- Leave-one-criterion-out: drop each criterion in turn and re-normalize; report rank stability.
- If available, report the weight-spread from the group-expert individual matrices as a
  real-judgement sensitivity band.

Outputs of sensitivity analysis are diagnostics. They do not authorize interpretation if any
other P1 gate (boundary, modelling unit, validation) is still open.

## 4. Blank Pairwise Comparison Template (7 Criteria)

Fill only the upper triangle. The lower triangle is the reciprocal and should be filled by the
HiWi after the session. Replace `<...>` placeholders with Saaty-scale integers or reciprocals
(e.g. `3`, `1/3`, `5`, `1/7`).

```csv
criterion,Flood,Sediment,LandUse,Environmental,Socioeconomic,Mining,Rehabilitation
Flood,1,<F-S>,<F-L>,<F-E>,<F-So>,<F-M>,<F-R>
Sediment,,1,<S-L>,<S-E>,<S-So>,<S-M>,<S-R>
LandUse,,,1,<L-E>,<L-So>,<L-M>,<L-R>
Environmental,,,,1,<E-So>,<E-M>,<E-R>
Socioeconomic,,,,,1,<So-M>,<So-R>
Mining,,,,,,1,<M-R>
Rehabilitation,,,,,,,1
```

After the session, the HiWi fills the lower triangle as the reciprocal of the upper triangle and
saves the completed matrix as a project registry artifact (NOT in
`ifpm-flood-pipeline/configs/`, which is public-safe).

## 5. Illustrative Structural Prior (NON-AUTHORITATIVE)

The matrix below is a STRUCTURAL prior derived from the methodology figure's three-tier
decomposition:

- Tier 1 (primary risk drivers): Flood Hazard, Sediment Risk.
- Tier 2 (vulnerability & exposure): Socioeconomic Vulnerability, Land Use / ASM, Environmental
  Sensitivity.
- Tier 3 (post-mining opportunity & value): Mining Location & Intensity, Rehabilitation
  Potential.

The encoding is: Flood > Sediment within Tier 1; Socioeconomic leads Tier 2; Mining leads Tier 3;
Tier 1 strongly dominates Tier 2; Tier 1 very strongly dominates Tier 3; Tier 2 moderately
dominates Tier 3.

### NON-AUTHORITATIVE BANNER

> This matrix is NOT project weights. It is an illustrative structural starting point for expert
> reaction only. It must NOT be used to generate any interpretable project output. It must NOT be
> copied into `ifpm-flood-pipeline/configs/`. Any real-data overlay using this matrix is a
> synthetic workflow diagnostic and must be labelled as such. Replace it with the elicited expert
> matrix before any V1 priority map is produced.

```csv
criterion,Flood,Sediment,LandUse,Environmental,Socioeconomic,Mining,Rehabilitation
Flood,1,2,5,5,4,7,7
Sediment,1/2,1,4,4,3,6,6
LandUse,1/5,1/4,1,1,1/2,3,3
Environmental,1/5,1/4,1,1,1/2,3,3
Socioeconomic,1/4,1/3,2,2,1,4,4
Mining,1/7,1/6,1/3,1/3,1/4,1,3
Rehabilitation,1/7,1/6,1/3,1/3,1/4,1/3,1
```

To check its CR (as a structural sanity check, NOT to adopt it):

```bash
uv run --directory ifpm-flood-pipeline ifpm-flood-pipeline ahp \
  --matrix <path-to-this-matrix.csv> --consistency-threshold 0.1
```

Expected behaviour: the clean tier ordering should produce CR <= 0.1. If it does not, that
indicates the tier encoding is internally inconsistent and the prior should be revised before
being shown to the expert. The implied weights are expected to be dominated by Flood Hazard and
Sediment Risk, with Rehabilitation Potential the smallest. Do not quote the implied weights as
project findings.

## 6. Use Rules

- The blank template and the illustrative prior stay in this internal file. They are not
  promoted to `configs/` until an elicited expert matrix exists AND the mentor approves its
  public-safe inclusion.
- Any CSV produced from an elicitation session is stored under
  `data/raw/<ahp_session_id>/` or a mentor-approved internal path, with a registry note, never
  in the public-safe deliverable tree.
- The `--allow-inconsistent` flag must not be used for any run whose output will be interpreted
  or shown to the mentor as a project result.
- Sensitivity outputs are diagnostics and do not override the NO-GO state of the real-data
  overlay gate.

## 7. Fallback

If no elicitation is completed before the deadline, follow the claim-boundary fallback in
`context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_ahp_weighting_decision_package_2026-06-15.md`: keep the pipeline runnable on synthetic data
only and label all outputs as workflow diagnostics.

## Next Step

Once the matrix is filled in, I run it through the pipeline's consistency check, apply it as a
sensitivity scenario on the prototype, and report both the resulting priority pattern and how
stable it is under weight changes.
