# Mentor-Facing Document Style

Applies to every file under `context/docs/mentor-explanation/` and to any short message, briefing,
or decision package sent to or written for the mentor.

The goal is documents that read as the HiWi's own work - clear, honest, human - not as an AI
process report.

## Voice

- Write in the **first person** ("I computed", "I found that", "my reading is"). The HiWi is the
  author and the one who did the work.
- Own errors directly ("the formula I was using is wrong"), not in the passive ("an error was
  found").
- State a personal judgment where you have one ("my reading is that..."), with the evidence behind
  it. Do not hide behind "it can be argued that".
- When the document needs a decision from the mentor, **say so plainly and firmly**: "I need your
  decision on X", "this is your call". Do not soften it into "I'd appreciate your guidance",
  "I was hoping to get your thoughts", or "it would be good to hear your view". The mentor is the
  decision-maker for thesis-level calls; asking weakly understates that the work is blocked on
  them. A direct ask respects their role and the dependency.

## Structure: state results, not the journey

- Lead with the conclusion or the single decision needed. Do not narrate the investigation step by
  step ("first I did X, then this triggered Y, which ended with Z").
- A reader should get the answer from the first paragraph. Background and method come after, and
  only as much as needed to support the answer.
- One question per message/briefing. If there are more, they belong in separate documents, not
  stacked.

## Remove AI-style scaffolding

Avoid these (they signal machine-generated text):

- "TL;DR", "Bottom line", "In summary", "To summarize" headers.
- Over-symmetric structure (every section the same length, mirror-image bullet pairs).
- Filler hedges that add nothing: "it is worth noting that", "it should be mentioned that".
- Emoji and decorative formatting in the body. Bold only for the one or two things that must stand
  out.
- Repetitive signposting ("As discussed above", "As we will see below").

## Plainness

- Short sentences. Plain words. No jargon a non-GIS reader has to stop on without a one-line
  gloss.
- Numbers in the text, not buried in a sentence: "R ≈ 500", not "the R factor, which was computed
  to be approximately five hundred".
- When you cite a finding, give the number and the source in the same line.

## Honesty over polish

- If something is uncertain, say so plainly and keep going ("ERA5 hourly is a lower bound on the
  true 30-minute R, so the real value is probably a bit higher").
- Do not over-claim. If the evidence supports "low group, roughly 4x below high group", write that;
  do not inflate it to "definitively proves".
- Carry the main caveat with the recommendation, not buried in a footnote.

## Scope of this rule

This style rule does NOT apply to internal engineering notes under `context/docs/project-management/`
or `context/docs/data-management/`, where traceable step-by-step records and full evidence chains
are wanted. It applies only to mentor-facing communication.
