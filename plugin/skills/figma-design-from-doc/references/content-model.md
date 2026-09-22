# `content.json` schema

Produced by `scripts/docx_extract.py`. Read the script's stdout outline first; only pull
specific parts of this file into context as you need them.

```jsonc
{
  "source": "/abs/path/to/doc.docx",
  "title": "Meet your team of AI Coworkers",
  "structure": "section-markers" | "headings" | "flat",
  "blocks":   [ /* flat, document order */ ],
  "sections": [ /* nested tree, derived from blocks */ ],
  "assets":   [ { "asset": "assets/image1.png", "bytes": 84213 } ],
  "stats":    { "blockCounts": {...}, "sectionCount": 9, "wordCount": 1840 }
}
```

## Block types

Every block has a `type`. Text-bearing blocks carry both `text` (plain, stripped) and
`runs` (styled spans).

| `type` | Fields |
|---|---|
| `heading` | `level` 1–6, `isTitle` (Word "Title" style), `text`, `runs` |
| `paragraph` | `text`, `runs`, `allBold`, `links[]`, plus convention fields below |
| `list` | `ordered`, `items[]` where each item is `{ level, text, runs }` |
| `table` | `header[]` (first row), `rows[]` (remainder), `allRows[]` (everything) |
| `image` | `asset` (path relative to `content.json`), `alt`, `widthPx`, `heightPx`; or `externalUrl` + `asset: null` for a linked image |
| `section_marker` | `sectionIndex`, `sectionTitle`, `text` |
| `placeholder` | `placeholder` (inside the brackets), `placeholderNote` (trailing text) |

A `run` is `{ text, bold, italic, underline, href }`. Adjacent runs with identical
formatting are merged, so `runs` is as short as the formatting allows. `bold` runs inside
an otherwise plain paragraph usually mark an inline subhead or a lead-in phrase.

## Convention fields on `paragraph`

Set when `docx_extract.py` recognises a page-spec convention:

- `marker: "labelled"` + `label` (the raw label, lowercased) + `role` (normalised) +
  `value` (text after the colon).
- `marker: "section"` → the block's `type` becomes `section_marker`.
- `marker: "placeholder"` → the block's `type` becomes `placeholder`.

Roles: `eyebrow`, `heading`, `subheading`, `body`, `cta`, `link`, `quote`, `attribution`,
`stat`, `metric`, `caption`, `note`, `meta`.

`role: "meta"` is SEO/CMS metadata (slug, meta description, SEO title) — **exclude it from
the design.**

## Section nodes

```jsonc
{
  "heading": "Delightful employee service, delivered autonomously",
  "level": 1,
  "index": 1,              // SECTION n number; null for heading-derived sections
  "kind": "section-marker" | "heading" | "preamble" | "root",
  "blocks": [ /* blocks belonging to this section */ ],
  "subsections": [ /* nested, heading structure only */ ],
  "roles": { "heading": ["..."], "body": ["..."], "cta": ["Get a demo"] },
  "placeholders": ["logo grid"]
}
```

`roles` and `placeholders` are the rolled-up signals — enough to choose an archetype
without walking the section's blocks.

## Section naming

For `section-markers` documents, a section is named by its `Heading:` label, else by its
first plain paragraph (truncated at ~90 chars), else `Section N`. A section left as
`Section N` is one that contains only a placeholder or a note — real content is missing and
Step 4 should say so.

## Edge cases the extractor already handles

- **Main part is not `word/document.xml`.** Google Docs exports often use
  `word/document2.xml`. Resolved through `_rels/.rels`.
- **Custom heading styles** without a `Heading N` style name — falls back to
  `w:outlineLvl`.
- **Bullets vs numbers** — resolved through `numbering.xml`, not guessed from the glyph.
- **Legacy VML images** from pasted screenshots, alongside modern DrawingML.
- **External (linked, not embedded) images** — emitted with `externalUrl` and
  `asset: null`. `use_figma` cannot fetch these; treat as a placeholder or upload the file
  separately.
- **Content controls** (`w:sdt`) and tracked insertions — descended into rather than
  skipped.

## Not handled

- Legacy binary `.doc`, `.rtf`, `.pages`, `.odt` — the script exits with a clear message
  asking for a `.docx` re-save.
- Headers, footers and footnotes (separate parts; rarely page content).
- Comments and tracked deletions — deletions are ignored, which is what you want.
- Multi-column section layouts and floating text boxes positioned absolutely.
