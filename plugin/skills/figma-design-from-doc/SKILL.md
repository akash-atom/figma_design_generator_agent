---
name: figma-design-from-doc
description: "Generate a desktop Figma design from a Word document using components from a pinned Figma component library. Use when the user wants to turn a .docx page spec, brief, blog post or content outline into a Figma layout, mock up a page from written content, or build a web page design in Figma from a document. Triggers on 'build this doc in Figma', 'generate a Figma design from this document', 'turn this Word doc into a design', 'design this page spec', or when a .docx is supplied alongside a Figma file or library."
---

# Desktop Figma design from a Word document

Turns a `.docx` into a 1440px desktop Figma frame assembled from a pinned component
library. You orchestrate; the Figma MCP server's own skills do the canvas work.

**Scripts live at `$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/`.** If that
variable is unset, resolve the path relative to this file. Both scripts are stdlib-only
Python 3 — never `pip install` anything.

Work in `./.figma-design/` in the user's current project: `config.json`, `content.json`,
`library-map.json`, `design-plan.md`, `assets/`.

---

## Step 0 — Resolve the component library

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/dgconfig.py" show
```

If `library.libraryKey` is null, **invoke the `figma-library-setup` skill and stop until it
completes.** This is the one-time "ask for the component library" step; every later run in
this project reads the saved value and asks nothing.

Never guess a library key.

## Step 1 — Resolve the target Figma file

If `targetFileKey` is already in the config, confirm it in one line and move on. Otherwise
ask the user (AskUserQuestion) between:

- **Existing file** — they paste a `https://figma.com/design/<fileKey>/...` URL. Extract
  `<fileKey>`. Strongly prefer this when the file already contains screens built from the
  library: Step 3 gets an authoritative component map for free.
- **New file** — read `skill://figma/figma-create-new-file/SKILL.md` via
  `ReadMcpResourceTool`, call `whoami`, use the single plan's `key` (ask which if there are
  several), then `create_new_file` with `editorType: "design"`.

Only `/design/` URLs work. Save the result:

```bash
python3 .../dgconfig.py set --file-key <FILEKEY> --doc <path/to/doc.docx>
```

## Step 2 — Extract the document

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/docx_extract.py" \
  "<path/to/doc.docx>" --out .figma-design/content.json
```

Read the printed outline — do **not** read the whole JSON into context. Pull specific
sections out with `python3 -c` or `jq` as you need them.

Then check the document against the page spec format:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/check_doc.py" \
  "<path/to/doc.docx>"
```

- **Errors** (exit 1) — report them to the user with the linter's suggested fixes and ask
  whether to fix the document or proceed anyway. Don't silently build from a doc with
  errors; a missing `Heading:` becomes a missing headline in the design.
- **Warnings** — carry them into the Step 4 plan as the places you had to guess. A "no
  `Layout:`" warning is exactly where your archetype choice needs the user's eye.
- **Long-form note** — the doc uses Word headings rather than the labelled format. That's
  expected for blog posts; proceed.

The authoring format is `references/doc-format.md`. When a document doesn't follow it,
point the user at that file (or at `templates/page-spec-template.docx` in the repo) rather
than explaining the format from scratch.

The script reports a `structure`, which tells you how to read the document:

| `structure` | What it means | How to treat it |
|---|---|---|
| `section-markers` | Plain-text `SECTION 1:` markers — the Atomicwork page-spec convention | One doc section = one page section. Highest fidelity; the author already did the layout thinking. |
| `headings` | Real Word heading styles (blog posts, long-form) | H1 = page title/hero, each H2 = a section, H3s group inside it. |
| `flat` | Neither | Propose a sectioning to the user in Step 4 before building. |

It also lifts three conventions out of plain paragraphs. **These are the highest-signal
input you have — use them over your own judgement about what a section should be:**

- **`role`** on a block, from a `Label: value` line. `eyebrow` (Tag:, Eyebrow:),
  `heading` (Heading:), `subheading`, `body` (Description:), `cta` (Button:, CTA:),
  `link`, `quote`, `attribution`, `stat`, `caption`, `note`, `meta`. `section.roles`
  aggregates them per section.
- **`placeholder`** — a line wrapped in `<...>` or `[...]`, e.g. `<logo grid>`,
  `<coworker grid>`, `<zuora testimonial block>`. **This names the component or visual the
  author wants.** Match it against the library map by name first.
- **`marker: "note"`** — author instructions ("On the left: ServiceNow and JSM logos").
  Honour them as layout direction; never render them as copy.

Blocks tagged `role: "meta"` (SEO title, slug, meta description) are **not page content** —
exclude them from the design.

## Step 3 — Build or reuse the library map

```bash
python3 .../dgconfig.py cache-status
```

On `HIT`, read `.figma-design/library-map.json` and skip to Step 4. On `MISS`/`STALE`,
discover it now, following `figma-generate-design` Step 2 with these adaptations:

1. **Code Connect discovery (its step 2a-i) is N/A.** The source is a document, not a
   codebase — there are no `*.figma.ts` files to glob. Log it as N/A and skip. Do not spend
   calls searching.
2. **Inspect existing screens first (2a-ii).** One `use_figma` call walking
   `findAllWithCriteria({ types: ["INSTANCE"] })` over an existing frame gives exact
   component keys. Do this whenever the target file has screens.
3. **`search_design_system` last (2a-iii)**, always scoped:
   `includeLibraryKeys: [<libraryKey from config>]`. One intent per `queries` entry, all in
   a single batched call. **Derive the query terms from the document** — the placeholders
   and section archetypes you found in Step 2 — not from a generic checklist. This tool
   rejects speculative synonym sweeps, and an empty result is not a reason to retry with
   variants.
4. Also collect `entity: "variable"` (color, spacing, radius) and `entity: "style"`
   (text, effect) results.
5. For each component you will actually use, instance it once in a scratch frame, read
   `componentProperties` (plus nested instances' properties), record the TEXT and VARIANT
   keys, then delete the scratch frame.

Write the result to `.figma-design/library-map.json`:

```json
{
  "libraryKey": "lk-...",
  "libraryName": "...",
  "discoveredAt": "2026-09-22",
  "components": {
    "Button": { "key": "abc123", "type": "COMPONENT_SET",
                "properties": { "Label#2:0": "TEXT", "Variant": "VARIANT" },
                "variants": ["Variant=Primary", "Variant=Secondary"] }
  },
  "variables": { "surface/default": { "key": "...", "type": "COLOR" } },
  "styles": { "heading/xl": { "key": "...", "type": "TEXT" } },
  "unmatched": ["<zuora testimonial block>"]
}
```

This cache is what makes the second run fast. Keep `unmatched` honest — it feeds Step 4.

## Step 4 — Write the section plan and get approval

Write `.figma-design/design-plan.md`, one row per page section:

| # | Doc section | Archetype | Component (variant) | Content mapping |
|---|---|---|---|---|
| 1 | S1 Delightful employee service… | hero | `Hero` (Variant=Centered) | eyebrow→`Tag#1:0`, heading→`Title#2:0`, body→`Body#3:0`, cta→nested `Button.Label#2:0` |

Archetypes to choose from: `hero`, `logo-band`, `feature-grid`, `feature-split`,
`stat-band`, `quote`, `accordion`, `table`, `cta-band`, `footer`.

Resolve each section's archetype in this order:

1. **`section.layout`** — the author's own `Layout:` line, already normalised. When it is
   set, use it. Don't second-guess it from the content.
2. **`section.placeholders`** — `<logo grid>` names the component.
3. **Content shape** — the fallback (see `references/section-mapping.md`).

`section.layoutDeclared` with a null `section.layout` means the author wrote a `Layout:`
value that isn't a known archetype; the linter already flagged it — say which section and
fall through to rule 2.

Then list, explicitly:

- Sections with **no component match** and the manual-build fallback you propose.
- Every image: `use_figma` **cannot fetch external image URLs**. For each extracted image in
  `.figma-design/assets/`, say whether you will `upload_assets` it or leave a labelled
  placeholder frame. Never silently leave a blank.
- Content you are dropping (meta blocks, author notes) and why.

**Stop here. Show the table and wait for the user's go-ahead.** Fixes are free now and
expensive once the canvas is written.

## Step 5 — Build

Load both Figma skills via `ReadMcpResourceTool` on `figma-remote-mcp`:

- `skill://figma/figma-use/SKILL.md` — mandatory before any `use_figma` call
- `skill://figma/figma-generate-design/SKILL.md` — the assembly workflow

Pass `skillNames: "resource:figma-use,resource:figma-generate-design"` on every `use_figma`
call. Then follow their Steps 3–4, with this project's desktop conventions from
`references/desktop-conventions.md` and `config.desktop`:

- Wrapper frame in **its own** `use_figma` call, vertical auto-layout, `frameWidth` (1440)
  wide, named after the document title. Return its ID.
- Build each section **directly inside** the wrapper, in retry-safe phases. Never build at
  page level and reparent — `appendChild` across calls silently fails.
- Bind colors with `setBoundVariableForPaint` and spacing/radii with `setBoundVariable`.
  Never hardcode a hex or a pixel value where the library has a token.
- Override instance text with `setProperties()` using the keys from `library-map.json`, not
  by assigning `node.characters`.
- Set `layoutSizingHorizontal = "FILL"` **after** appending, not before.

## Step 6 — Validate

One `get_screenshot` of the wrapper frame. Check for:

- leftover placeholder strings ("Title", "Heading", "Button", "Lorem")
- clipped or overlapping text
- wrong component variants
- blank image frames
- **the font family** — assert it explicitly against the library's own text styles; a script
  can load the wrong font without erroring

Apply targeted fixes, take one post-fix screenshot, then report the Figma URL, the section
count, and anything you left as a placeholder or could not map.

---

## References

- `references/doc-format.md` — the page spec format documents should follow
- `references/content-model.md` — the `content.json` schema and its edge cases
- `references/section-mapping.md` — archetype selection rules
- `references/desktop-conventions.md` — frame sizing, spacing rhythm, naming

## Failure modes

- **`.doc` / Pages / Google Docs `.gdoc`** — unsupported. Ask for a `.docx` re-save. The
  extractor already handles Google Docs `.docx` exports, including ones whose main part is
  `word/document2.xml`.
- **Document has no headings and no `SECTION n:` markers** — `check_doc.py` errors on
  this. Don't invent structure silently: show the user `references/doc-format.md`, offer
  `templates/page-spec-template.docx`, and if they want to proceed anyway, propose a
  sectioning in Step 4 for them to correct.
- **Library has no match for a placeholder** — build it manually from primitives bound to
  library variables, and say so in the final report. Do not substitute a component that
  merely looks close.
