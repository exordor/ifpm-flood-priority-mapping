# AI Research Document Generation: Lessons Learned

## 1. Core Lesson

This workflow showed that AI can be very useful for research-document preparation, but only if the process is controlled like a research workflow, not like simple text generation.

The most important lesson is:

> AI should help collect, structure, compare, and revise information, but the final document must be evidence-based, human-readable, source-checked, and free of AI process traces.

For this project, the best workflow was not "generate one final document immediately". The better workflow was:

1. Preserve the original document.
2. Convert the original into an editable Markdown source.
3. Create a separate reviewed version.
4. Research and verify dataset links.
5. Clean AI-style wording and reasoning traces.
6. Keep Markdown as the source of truth.
7. Export DOCX/PDF only after the content is stable.

## 2. What Worked Well

### Non-Destructive Editing

Keeping the original document unchanged was the right decision.

The original inventory stayed under `docs/original/`, while the reviewed version was created separately under `docs/research-review/`. This made the work safer because the review could be improved without damaging the original file sent by the mentor.

Reusable rule:

> When reviewing someone else's document, do not overwrite the original. Create a clearly named reviewed version.

### Turning The Mentor's Email Into A Checklist

The mentor's request was broad, but it became manageable after converting it into concrete checks:

- dataset availability and suitability;
- real dataset links;
- GIS preprocessing requirements;
- AHP-MCDA weighting and consistency;
- mining-location and rehabilitation-potential criteria;
- gaps and validation datasets before modelling.

This prevented the review from becoming a general essay.

Reusable rule:

> Convert supervisor or mentor feedback into a checklist before writing.

### Markdown As Source Of Truth

Markdown worked well as the main version-controlled format.

It made it easier to:

- review diffs in Git;
- edit text cleanly;
- search for weak wording;
- remove AI-style phrases;
- regenerate DOCX/PDF later.

DOCX and PDF are useful deliverables, but they are harder to diff and should not be the primary working source.

Reusable rule:

> Keep Markdown under version control. Treat DOCX/PDF as exports.

### Manual URL Verification

Manual link checking was necessary.

Some URLs looked valid from search results but were not usable in practice. For example, the newer `gob.pe/ana` route was usable while some older ANA legacy links were not accessible from the current environment.

Reusable rule:

> A URL is not confirmed just because it appears in a source. It must be opened or otherwise verified.

### Separating Open Links From Data Readiness

A major improvement was distinguishing between:

- a web page can be opened;
- a dataset can be downloaded;
- licence terms are acceptable;
- an account or request is required;
- the GIS layer is complete and usable;
- the data are suitable for modelling.

This distinction made the review more honest and defensible.

Reusable rule:

> "Reachable link" does not mean "modelling-ready dataset".

### Human-Readable Mentor Explanation

The oral explanation documents were useful because they translated the technical review into meeting language.

The best structure was:

- one-sentence project explanation;
- two-minute speaking script;
- answers to the mentor's requested points;
- technical cautions;
- questions to ask the mentor;
- short version for quick discussion.

Reusable rule:

> A research review and an oral explanation are different documents. Do not expect one document to serve both purposes.

## 3. Main Problems Encountered

### AI-Style Helper Phrases

Some phrases made the document look like an AI-generated support document instead of a normal research document.

Examples of wording to avoid:

- "Prepared as a reviewed, non-destructive companion document..."
- "The original files are not modified."
- "This companion review..."
- long explanations of why the document exists;
- visible descriptions of the AI workflow.

These may be useful during drafting, but they should not remain in a document sent to a mentor.

Better approach:

> State the research content directly. Keep workflow notes in project notes, not in the final review document.

### Visible Reasoning Traces

The review initially contained too much process language: what was checked, why it was checked, and how the review was constructed.

This can make the document feel less human because academic documents usually present results, evidence, assumptions, and limitations, not the author's internal drafting process.

Better approach:

> Keep conclusions, evidence, limitations, and next steps. Remove internal thought process.

### Over-Polishing The Export Format

Changing to a more "academic" font style made the exported document look worse than the default conversion.

The lesson is that formatting should match the document's practical use. A simple default Word/Pandoc style can be better than forcing a formal style if the result reduces readability.

Better approach:

> Do not change typography unless it clearly improves readability in the actual target application.

### PDF/DOCX Export Issues

The export process created a link problem:

- the DOCX contained real hyperlinks;
- the PDF renderer introduced visible unwanted characters after URLs;
- the issue came from the conversion/rendering chain, not from the Markdown source.

This showed that export quality must be checked in the final format, especially for clickable links.

Better approach:

> Test final DOCX/PDF links after export. If the renderer changes URL appearance or link behaviour, stop and change the export method.

### Generating Multiple Formats Too Early

Exporting DOCX/PDF before the content was stable caused avoidable rework.

The better decision was to wait until:

- links had been manually verified;
- AI-style wording was removed;
- readability had been checked;
- the user confirmed the content was stable.

Better approach:

> Do not generate final export formats while the Markdown source is still changing frequently.

### Git And Binary Files

PDF and DOCX files caused unnecessary version-management noise.

The project became cleaner after treating Markdown as the version-managed source and ignoring binary exports.

Better approach:

> Track source documents. Ignore generated binary outputs unless a specific final deliverable must be archived.

## 4. Research Quality Lessons

### Dataset Links Need Source Hierarchy

Not all links are equal.

Preferred order:

1. official data download page;
2. official product landing page;
3. official data portal;
4. institutional information page;
5. secondary documentation;
6. general search result or news page.

For the review, official product pages and download portals were better than broad institutional pages when available.

### Country-Specific Data Need Different Confidence Levels

Peru and Zimbabwe did not have the same level of official data accessibility.

Peru had clearer routes for mining information through INGEMMET/GEOCATMIN and hydrological authority entry points through `gob.pe`/ANA/SNIRH.

Zimbabwe had official mining cadastre and institutional sources, but the review needed to state that cadastre data may be provisional and should be validated.

Reusable rule:

> Do not force equal confidence across countries just because the study is comparative.

### Dataset Suitability Is Not Only Technical Resolution

A dataset can have good resolution but still be unsuitable for a specific modelling role.

Examples:

- WorldCover is useful for land-cover baseline, but not enough for direct land-use change proof.
- RUSLE is useful for erosion screening, but not enough for actual sediment delivery.
- Mining concessions are useful for official rights, but not proof of active mining.
- AHP-MCDA is useful for priority ranking, but not a physical flood-inundation model.

Reusable rule:

> Always define what each dataset can and cannot support.

### Validation Must Be Designed Before Modelling

Validation cannot be added as an afterthought.

For this study, validation options include:

- historical flood records;
- EM-DAT;
- Dartmouth Flood Observatory;
- Copernicus EMS;
- GloFAS or global flood products;
- satellite-derived flood extents;
- local rainfall or hydrometric records;
- expert or community validation.

Reusable rule:

> Define the validation package before finalizing weights and indicators.

## 5. Writing Quality Lessons

### Keep The Final Review Direct

A mentor-facing research review should not read like an explanation of how AI worked.

Better final-document style:

- "Recommended source..."
- "Use and limitations..."
- "Preprocessing requirements..."
- "Remaining gap..."
- "Decision required before modelling..."

Avoid:

- "I checked..."
- "This document was prepared as..."
- "The review process found..."
- "This AI-generated companion..."

### Separate Audiences

Different audiences need different documents:

- research review: technical detail and evidence;
- mentor email: short, polite, action-oriented;
- oral explanation: simple speaking script;
- internal lessons learned: workflow notes and mistakes.

Reusable rule:

> Do not overload one document with every purpose.

### Make Limitations Explicit But Not Defensive

Good limitation wording is concise and technical.

Better:

> Manual URL checks confirm reachability, but not account approval, licence acceptance, bulk download success, or GIS-ready geometry quality.

Worse:

> Because I used AI and some sources may be uncertain, please note that this is only a companion document.

## 6. Recommended Future Workflow

For future AI-assisted research-document generation, use this order:

1. Save the original document unchanged.
2. Convert the original to Markdown if needed.
3. Create a separate reviewed Markdown file.
4. Convert the mentor or supervisor request into a checklist.
5. Build a dataset register with official links, access conditions, suitability, limitations, and preprocessing notes.
6. Verify priority links manually.
7. Separate confirmed facts from assumptions and pending checks.
8. Remove AI-style wording and internal reasoning traces.
9. Do a readability pass.
10. Keep Markdown in Git.
11. Generate DOCX/PDF only after the text is stable.
12. Check exported links, fonts, page breaks, and tables in the final format.
13. Prepare a short email and oral explanation separately from the technical review.

## 7. Practical Checklist Before Sending A Mentor-Facing Document

Before sending, check:

- Are original files preserved?
- Is the reviewed file clearly separate?
- Are all major claims tied to a source or explicit assumption?
- Are dataset links real and manually checked?
- Are broken or legacy URLs removed or downgraded?
- Are access constraints stated?
- Are GIS preprocessing steps specific enough?
- Are AHP weights described as pending expert judgement, not already fixed?
- Are mining concessions separated from active mining?
- Is rehabilitation need separated from rehabilitation feasibility?
- Are validation datasets identified?
- Are AI-style helper phrases removed?
- Are internal reasoning traces removed?
- Is the document readable to a human mentor?
- Are DOCX/PDF exports generated only after the Markdown source is stable?
- Are exported hyperlinks clickable?

## 8. Final Takeaway

The strongest result came from using AI as a research assistant and editor, not as an automatic final-document writer.

The process should stay evidence-first:

> Use AI to accelerate structure, comparison, and drafting; use human judgement to verify sources, clean the writing, choose the final format, and decide what is ready to send.
