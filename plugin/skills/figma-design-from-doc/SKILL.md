---
name: figma-design-from-doc
description: "Design a desktop Figma page from a Word document, making all the layout decisions so the writer doesn't have to. Reads the content, works out the sections and the right component for each, then builds it from a pinned Figma component library. Use when the user wants to turn a .docx brief, page spec, blog post, content outline or raw copy into a Figma design, mock up a page from written content, or build a web page design in Figma from a document. Triggers on 'build this doc in Figma', 'generate a Figma design from this document', 'turn this Word doc into a design', 'design this content', 'make a page from this copy', or when a .docx is supplied alongside a Figma file or library."
---

# Desktop Figma design from a Word document

Turns a `.docx` into a 1440px desktop Figma frame assembled from a pinned component
library. You orchestrate; the Figma MCP server's own skills do the canvas work.

**The writer supplies content. You supply every design decision.** Documents arrive as
plain copy with no markup, and that is the expected case — not a problem to be corrected.
Work out the sections, the archetypes and the component for each yourself.

Two rules govern the whole pipeline, and `references/inference.md` is where they are
worked out:

> **Decide about design. Ask about copy.** Layout, archetype, variant, order and splitting
> are yours to decide — state what you chose and why. The writer's words are theirs:
> never silently rewrite, shorten, retitle or invent copy to make it fit a component.

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

**If the library is unpublished, build into the library file itself** — set
`targetFileKey` to `libraryFileKey` and add a page to it. Local components instance
directly, so nothing needs publishing. `dgconfig.py show` reports this as
`resolved mode: local`.

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

Then check that there is enough content to design from:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/check_doc.py" \
  "<path/to/doc.docx>"
```

This checks only what the **writer** controls — enough copy, an opening line per section,
a closing ask, no placeholder text, pasted rather than linked images. It says nothing
about layout.

- **Errors** (exit 1) — missing or unusable content. Report them and ask how to proceed.
- **Warnings** — compromises the design will have to make. Carry them into the Step 4 plan.
- Nothing here is about formatting. **Never tell the writer to restructure their document
  to suit the tool.**

Add `--format` only if the user has opted into the optional markup in
`references/doc-format.md` and wants it validated.

The document's structure (`section-markers`, `headings`, `flat`) tells you where the
section boundaries come from. `flat` — no headings, no markers, just typed paragraphs — is
a perfectly normal input; Step 3 infers the boundaries.

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

## Step 3 — Work out the design

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/analyze_content.py" \
  .figma-design/content.json --out .figma-design/analysis.json
```

**Read `references/inference.md` before interpreting the output.** It is the decision
guide: how to read the signals, how to fill component slots from unlabelled prose, when to
split or merge sections, and what to do with copy no component can hold.

The analyser proposes a section list with a ranked archetype per section, scored reasons,
split suggestions and page-level notes. It is a proposal — it measures the shape of the
writing and cannot see your component library. Override any row the library contradicts,
and say that you did.

Three outputs decide the rest of the run:

- **`documentKind`** — `article` means long-form prose with no call to action. **Do not
  build it as a marketing page**; build a title block and a single measure-constrained
  column of copy, and say that's what you read it as. `marketing-page` gets the full band
  treatment. `mixed` — pick one and say which.
- **`pageNotes`** — whole-page problems: no hero, no CTA, no visual relief, adjacent
  duplicate bands, sections too heavy for any component.
- **`confidence`** per section — `low` rows are the ones to decide from the library and
  the neighbouring sections rather than from the score.

Use the archetypes this produces to derive the `search_design_system` query terms in
Step 4 — that keeps the search scoped to what the page actually needs.

## Step 4 — Build or reuse the library map

```bash
python3 .../dgconfig.py cache-status
```

On `HIT`, read `.figma-design/library-map.json` and skip to Step 5. On `MISS`/`STALE`,
discover it now. This follows `figma-generate-design` Step 2, but the ordering differs
because the source is a document, not a codebase:

**1. Code Connect discovery (its step 2a-i) is N/A.** There are no `*.figma.ts` files to
glob. Log it as N/A and skip — don't spend calls searching.

**2. If `library.libraryFileKey` is set, read the library file directly.** This is the
best path by a wide margin: it is exact, complete, and needs no example screen. Run
`use_figma` against the *library* file:

```js
// Components usually live on one page. Switch to it if it isn't current --
// loadAllPagesAsync is not available, so enumerate one page at a time.
const page = figma.root.children.find(p => /component|library|main/i.test(p.name))
  || figma.currentPage;
if (page.id !== figma.currentPage.id) await figma.setCurrentPageAsync(page);

const sets = new Map();
for (const n of figma.currentPage.findAllWithCriteria({
  types: ["COMPONENT_SET", "COMPONENT"] })) {
  // A variant's own componentPropertyDefinitions throws -- always read the set.
  const set = (n.type === "COMPONENT" && n.parent?.type === "COMPONENT_SET")
    ? n.parent : n;
  if (sets.has(set.id)) continue;
  sets.set(set.id, {
    name: set.name,
    id: set.id,        // use this in local mode
    key: set.key,      // use this in published mode
    type: set.type,
    properties: set.componentPropertyDefinitions,
    variants: set.type === "COMPONENT_SET"
      ? set.children.map(c => c.name) : null,
  });
}
return { page: figma.currentPage.name, count: sets.size,
         components: [...sets.values()] };
```

`componentPropertyDefinitions` gives the TEXT, VARIANT, BOOLEAN and INSTANCE_SWAP keys
directly — **no scratch instances needed.** If the response is too large, return
`{name, key}` only, then re-read `componentPropertyDefinitions` for the subset the page
actually needs. If the components turn out to span several pages, repeat per page.

**3. Otherwise, inspect existing screens in the target file (2a-ii).** When you only have
a consumer file, walk its instances:
`findAllWithCriteria({ types: ["INSTANCE"] })`, then `inst.mainComponent` and up to its
`COMPONENT_SET` parent. Main components are not `INSTANCE` nodes, so this path only sees
what has actually been placed.

**4. `search_design_system` last (2a-iii)**, always scoped:
`includeLibraryKeys: [<libraryKey from config>]`. One intent per `queries` entry, all in a
single batched call. **Derive the query terms from the archetypes in Step 3** — not from a
generic checklist. This tool rejects speculative synonym sweeps, and an empty result is
not a reason to retry with variants.

**5. Also collect** `entity: "variable"` (color, spacing, radius) and `entity: "style"`
(text, effect) results. In the library file, `figma.variables.getLocalVariableCollectionsAsync()`
lists local variables directly.

**Record both `id` and `key` for every component**, plus the resolved `mode`, in
`library-map.json`. Which one you use in Step 6 depends on the mode.

**If a component key fails to import in published mode**, the library is unpublished. Do
not fall back to hand-built frames — switch to local mode instead (build into the library
file), which needs no publishing and produces real instances. Say so plainly.

Write the result to `.figma-design/library-map.json`:

```json
{
  "libraryKey": "lk-...",
  "libraryFileKey": "...",
  "libraryName": "...",
  "mode": "local",
  "discoveredAt": "2026-09-24",
  "components": {
    "Button": { "id": "12:34", "key": "abc123", "type": "COMPONENT_SET",
                "properties": { "Label#2:0": "TEXT", "Variant": "VARIANT" },
                "variants": ["Variant=Primary", "Variant=Secondary"] }
  },
  "variables": { "surface/default": { "key": "...", "type": "COLOR" } },
  "styles": { "heading/xl": { "key": "...", "type": "TEXT" } },
  "unmatched": ["<zuora testimonial block>"]
}
```

This cache is what makes the second run fast. Keep `unmatched` honest — it feeds Step 4.

## Step 5 — Write the section plan and get approval

Write `.figma-design/design-plan.md`, one row per page section:

| # | Doc section | Archetype | Component (variant) | Content mapping |
|---|---|---|---|---|
| 1 | S1 Delightful employee service… | hero | `Hero` (Variant=Centered) | eyebrow→`Tag#1:0`, heading→`Title#2:0`, body→`Body#3:0`, cta→nested `Button.Label#2:0` |

Archetypes to choose from: `hero`, `logo-band`, `feature-grid`, `feature-split`,
`stat-band`, `quote`, `accordion`, `table`, `cta-band`, `footer`.

Take the archetypes from Step 3's analysis. Resolve each section in this order:

1. **`section.layout`** — an explicit `Layout:` line, if the author wrote one. Honour it.
2. **`section.placeholders`** — `<logo grid>` names the component.
3. **The analyser's top candidate** where `confidence` is `high`.
4. **Your own reading** of `signals` against the library for `medium` and `low`, per
   `references/inference.md`.

Apply the analyser's `split` suggestions and `pageNotes` here: split a section that holds
both copy and a visual, vary adjacent duplicate bands, and alternate surfaces so bands
read as distinct.

Write each row as a **decision with its reason**, not as a question:

> 3 → feature-grid (`Cards / Feature`, Variant=3-up). Six parallel paragraphs averaging
> 18 words read as cards; split each on its first full stop into title and body.

Then list, explicitly:

- Sections with **no component match** and the manual-build fallback you propose.
- Any copy that **cannot fit** the component you chose, with the specific edit you would
  make — before and after. **Wait for a yes on these.** Never trim a headline, summarise a
  paragraph or invent a button label to make the layout work.
- Anything the analyser flagged at `low` confidence, and what you decided instead.
- Every image: `use_figma` **cannot fetch external image URLs**. For each extracted image in
  `.figma-design/assets/`, say whether you will `upload_assets` it or leave a labelled
  placeholder frame. Never silently leave a blank.
- Content you are dropping (meta blocks, author notes) and why.

**Stop here. Show the table and wait for the user's go-ahead.** Fixes are free now and
expensive once the canvas is written. Present the design decisions as made — the user can
overrule any of them — and block only on the copy questions above.

## Step 6 — Build

Load both Figma skills via `ReadMcpResourceTool` on `figma-remote-mcp`:

- `skill://figma/figma-use/SKILL.md` — mandatory before any `use_figma` call
- `skill://figma/figma-generate-design/SKILL.md` — the assembly workflow

Pass `skillNames: "resource:figma-use,resource:figma-generate-design"` on every `use_figma`
call. Then follow their Steps 3–4, with this project's desktop conventions from
`references/desktop-conventions.md` and `config.desktop`:

**Resolving components, variables and styles depends on the mode:**

| | local (same file, unpublished OK) | published (cross-file) |
|---|---|---|
| Component | `figma.getNodeByIdAsync(id)` | `figma.importComponentSetByKeyAsync(key)` |
| Variable | `figma.variables.getVariableByIdAsync(id)` | `figma.variables.importVariableByKeyAsync(key)` |
| Style | `figma.getStyleByIdAsync(id)` | `figma.importStyleByKeyAsync(key)` |

Both then behave identically — `set.children.find(...)` for the variant, `createInstance()`,
`setProperties()`, `setBoundVariable`. In local mode nothing is imported, so **publishing
is never required**; list the local collections with
`figma.variables.getLocalVariableCollectionsAsync()` and
`figma.getLocalTextStylesAsync()`.

In local mode, add the page rather than assuming one:
`const page = figma.createPage(); page.name = "<Document title>"; await figma.setCurrentPageAsync(page);`
Keep the build off the components page so the library stays tidy.

- Wrapper frame in **its own** `use_figma` call, vertical auto-layout, `frameWidth` (1440)
  wide, named after the document title. Return its ID.
- Build each section **directly inside** the wrapper, in retry-safe phases. Never build at
  page level and reparent — `appendChild` across calls silently fails.
- Bind colors with `setBoundVariableForPaint` and spacing/radii with `setBoundVariable`.
  Never hardcode a hex or a pixel value where the library has a token.
- Override instance text with `setProperties()` using the keys from `library-map.json`, not
  by assigning `node.characters`.
- Set `layoutSizingHorizontal = "FILL"` **after** appending, not before.

## Step 7 — Validate

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

- `references/inference.md` — **read this before Step 3.** How to turn content into design
  decisions, and the rules on not rewriting the writer's copy
- `references/content-model.md` — the `content.json` schema and its edge cases
- `references/doc-format.md` — the *optional* markup an author can add to override your
  choices. Never required
- `references/section-mapping.md` — archetype selection rules
- `references/desktop-conventions.md` — frame sizing, spacing rhythm, naming

## Failure modes

- **`.doc` / Pages / Google Docs `.gdoc`** — unsupported. Ask for a `.docx` re-save. The
  extractor already handles Google Docs `.docx` exports, including ones whose main part is
  `word/document2.xml`.
- **Document has no headings and no markers** — normal, not an error. The analyser infers
  section boundaries from paragraph shape. Report the sectioning you inferred in the Step 5
  plan so the user can correct it. Don't ask them to restructure the document.
- **Long-form article** — `documentKind: "article"`. Build a title block and a single
  column of prose, not a page of bands. Say which treatment you chose.
- **Copy too long for any component** — lay it out at the length it is, or propose a
  specific cut and wait. Never silently shorten it.
- **Library has no match for a placeholder** — build it manually from primitives bound to
  library variables, and say so in the final report. Do not substitute a component that
  merely looks close.
