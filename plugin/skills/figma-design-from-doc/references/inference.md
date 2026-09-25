# Designing from content

The writer supplies content. **You supply every design decision.** They should not have to
think about layout, sections, component names or formatting — and they should not be asked
to.

## The governing rule

> **Decide about design. Ask about copy.**

Layout, archetype, variant, order, spacing, which component, how to split a section — those
are yours. Decide them, state what you decided and why, and let the user overrule you if
they want to.

Copy is theirs. **Never silently rewrite, shorten, split, retitle or invent the writer's
words to make them fit a component.** If a 300-word paragraph won't fit the card you want,
you have three honest options, in order of preference:

1. Use a component that fits the copy as written (a prose block, an accordion row).
2. Lay the copy out manually at the length it is.
3. Propose a specific edit — show the before and after — and wait for a yes.

The same applies in reverse when there is **too little** copy: build fewer instances
rather than repeating content. A card duplicating another card's real title and body is
indistinguishable from finished work, which makes it worse than an obviously empty slot.

Inventing a button label, trimming a headline to fit one line, or summarising a paragraph
into a card is the one failure that makes this tool untrustworthy. A design that is slightly
less tidy but says exactly what the writer wrote is always the better outcome.

## Start from the analysis

`scripts/analyze_content.py` reads `content.json` and writes `analysis.json`: candidate
sections, a proposed archetype for each with scored reasons, split suggestions, and
page-level notes.

It is a **proposal, not a verdict.** It measures shape; it cannot see your component
library. Override any row when the library says otherwise — and say you did, with the
reason. Its `reasons` fields exist to be argued with.

Read in this order:

1. **`documentKind`** — `article`, `marketing-page` or `mixed`. This decides everything
   downstream. See below.
2. **`pageNotes`** — whole-page problems: no hero, no CTA, no visual relief, adjacent
   duplicate bands, sections too heavy for any component.
3. **Per section**: `proposed`, `confidence`, `candidates`, `split`, `signals`.

`confidence: "low"` means the shape was ambiguous. Those are the rows to decide from the
library and the surrounding sections, not from the score.

## `documentKind` comes first

**`article`** — mostly prose, no calls to action. A blog post, a launch note, an opinion
piece. **Do not lay it out as a marketing page.** Hero-plus-bands will stretch a few
hundred words of argument across a page of half-empty sections. Build an article instead:

- A title block: title, optional standfirst, byline/date if the source has one.
- One measure-constrained column (~640–720px inside the 1440 frame) of the library's body
  text style. Do not widen prose to 1200px.
- Pull out a quote or a statistic where the copy already offers one — that is visual
  relief that costs the writer nothing.
- Say plainly that you read it as an article, and offer the page treatment as the
  alternative.

**`marketing-page`** — structured sections, an ask at the end. Full band layout, the
archetypes below.

**`mixed`** — say so and pick one, with your reasoning. Don't build half of each.

## Choosing an archetype

Resolve in this order; stop at the first that answers.

1. **The author's `Layout:` line**, if present (`section.layout`). Honour it.
2. **A `<placeholder>`** naming a component. `<logo grid>` means a logo band.
3. **The analyser's top candidate**, when `confidence` is `high`.
4. **Your own reading** of `signals` against the library, for `medium` and `low`.

The signals worth understanding, because they are where writers leak structure without
meaning to:

| Signal | What it tells you |
|---|---|
| `implicitItemCount` | Consecutive `Lead-in. Body.` paragraphs — **cards the writer never bulleted.** The single most useful signal on unstructured docs. |
| `implicitItemWordsAvg` / `listItemWordsAvg` | Over ~40 words an item cannot be a card. Accordion or prose. |
| `listItemsParallel` | Similar-length items grid cleanly. Wildly uneven ones look broken in a grid — stack them or use an accordion. |
| `metricItems` | Numbers with units or percentages — a stat band. |
| `questionItems` | Questions — an accordion/FAQ, whatever the item count. |
| `closingImperative` | Ends on "Get started", "Book a demo" — a CTA band. |
| `hasQuoteMarks` + `hasAttribution` | A testimonial, even unlabelled. |
| `longestParagraphWords` | Over ~90, no card component will hold it. |
| `unlabelledParagraphCount` | Raw prose you have to assign to slots yourself. |

## Filling slots from unlabelled prose

When a section has no labels at all, assign roles yourself:

- **Heading** — the section's heading if it has one; otherwise the first short line
  (≤16 words, no terminal full stop).
- **Eyebrow** — only if the source actually has a short standalone label above the
  heading. **Don't invent one.**
- **Body** — the paragraph or paragraphs after the heading. If there are several and the
  component takes one, use them all in one text node rather than dropping any.
- **Items** — bullets, or a run of parallel paragraphs. Split each on its first `.`, `—`
  or `:` into title and body; if an item has no such break, it is title-only, and then
  *every* item in that section is title-only.
- **CTA** — only from copy that is actually an instruction to the reader. A heading that
  happens to start with a verb is not a button. **If there is no CTA copy, leave the
  button out** and note it; do not write "Learn more".

## Splitting and merging

Writers group content by topic, not by page section. Fix it yourself:

- **Split** when `split` is set, or when one section holds both substantial copy and a
  visual placeholder, or a long argument plus a list. Two clean bands beat one crowded one.
- **Merge** a heading that only introduces its children into the first child. The analyser
  already merges heading-less fragments forward.
- **Reorder** only for a real reason, and say so. A logo band belongs right after the hero
  even if the writer put it last; the order of argument sections is the writer's.

## When the library has no component for a section

A design system rarely ships a component per page section. It ships **molecules** — a
heading block, a card, an icon row, a logo strip — and expects sections to be *composed*
from them. Composing is the normal path, not the fallback.

In order:

1. **A section-level component**, if one exists for this archetype.
2. **A different variant** of a near component, if it genuinely fits the content.
3. **Compose the section from smaller library components.** Build the section container
   and its layout yourself — an auto-layout frame, a grid, a row — and fill it with
   library instances. A `feature-grid` with no grid component is a frame containing a
   `Heading Block` instance and N `Card` instances. This is a real design-system result:
   every piece stays linked and updates with the library. Only the container is yours.
4. **Build from primitives** — frames and text bound to library variables and text styles
   — for the parts no component covers. Say in the report that these are not instances.
5. **A labelled placeholder** only when the content itself is missing, or nothing in the
   library gets close.

Reach for 5 far less often than feels natural. A placeholder is right for *absent
content*; it is the wrong answer to *absent component* when the library has the pieces to
build one.

Use `granularity` in `library-map.json` to see what is composable: `section` components
stand alone, `molecule` components are what you compose from, `atom` components fill slots
inside molecules. A component's own description often says which it is.

Never force content into a component that changes its meaning — a three-item stat band
rendered as feature cards reads as three features, not three numbers. Composing from
molecules is not forcing; substituting a different section type is.

## Page rhythm

Once the archetypes are chosen, look at the sequence:

- Opens with a hero, closes with a CTA (if the copy supports one).
- No two adjacent identical bands unless the content genuinely repeats. Vary the archetype,
  or alternate background surface and media side.
- Alternate surface fills so bands read as distinct.
- Visual relief every three or four sections — a quote, a stat band, a split with media.
- A run of five text-only sections is a page nobody scrolls. If the copy offers nothing to
  break it, say so rather than inventing a visual.

## What to tell the user

Present the plan as **decisions with reasons**, not questions:

> Section 3 → feature-grid (`Cards / Feature`, Variant=3-up). Six parallel paragraphs
> averaging 18 words read as cards; I split each on its first full stop into title and
> body.

Ask only where the answer changes their **content**: copy that must be cut to fit, a
missing CTA you would otherwise omit, an image you cannot place. Everything else you
decided — list it so they can push back, but don't block on it.
