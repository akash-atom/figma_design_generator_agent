# Figma Design Generator

A Claude Code plugin that turns a Word document into a desktop Figma design built from
components in your own Figma component library.

Give it a `.docx` page spec or brief; it extracts the content, plans which library
component fills each section, shows you the plan, then builds and validates a 1440px frame
in Figma.

## Install (teammates)

```
/plugin marketplace add akash-atom/figma_design_generator_agent
/plugin install figma-design-generator
```

That's it — the plugin ships the Figma MCP server config, so you get the Figma connection
too. You'll be asked to authenticate with Figma on first use.

To get updates later:

```
/plugin update figma-design-generator
```

## Use

```
/figma-design-from-doc
```

Then point it at your document. On the first run in a project it asks which Figma
component library to build with and remembers the answer.

Related:

```
/figma-library-setup      # change or inspect the pinned component library
```

## What happens

1. **Library** — pinned once per project, cached in `.figma-design/config.json`.
2. **Target file** — a new Figma file, or a new frame in a file you paste the URL of.
   Pointing at a file that already has screens gives better results: the components can be
   read straight off the existing work.
3. **Extract** — `.docx` → `.figma-design/content.json`, with images pulled out to
   `.figma-design/assets/`.
4. **Design** — the content is analysed into sections, each scored against ten layout
   archetypes with reasons, plus split suggestions and page-level notes (no hero, no CTA,
   no visual relief, two identical bands in a row). Blog posts are detected and laid out
   as articles rather than marketing pages.
5. **Plan** — a section-by-section table of the component and variant chosen for each, and
   which copy goes in which slot, **presented as decisions with reasons.** You approve it
   before anything is written to Figma.
6. **Build** — a 1440px frame of real library component instances, with colours and spacing
   bound to library variables.
7. **Validate** — one screenshot pass for clipped text, wrong variants, leftover
   placeholders and the wrong font.

## What the writer has to do

**Write the content. Nothing else.** No headings, no markup, no layout decisions — a
document of plain typed copy is the expected input, and the design is worked out from it:

- where the sections start and end, even with no headings at all
- what each section should be (hero, card grid, stat band, quote, closing CTA...)
- when a section is really two, and splitting it
- when a run of prose paragraphs is actually a set of cards
- which library component fits, and which copy goes in which slot
- whether the document is a page at all, or a blog post that wants an article layout

Send writers to **[DOC-FORMAT.md](DOC-FORMAT.md)**. It's one page, and most of it is about
writing well rather than formatting.

Two guarantees it makes on their behalf: **copy is never rewritten to fit a component**
(a component that fits is chosen instead, or a specific edit is proposed and confirmed),
and **nothing is invented** — no filler headlines, no "Learn more" buttons they didn't
write.

Check a document has enough to work with:

```bash
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py "My page.docx"
```

It reports only what a writer controls — thin content, a section with no opening line,
placeholder text, a paragraph too long to lay out, a linked image — and says nothing about
layout. Exits 1 on errors so it can gate a workflow. The skill runs it automatically.

### Optional markup, for when you do have a layout in mind

A `Layout: feature-grid` line on a section, or a `<logo grid>` placeholder, overrides the
inferred choice. Use it on one section or none; it is never required. Full reference:
[references/doc-format.md](plugin/skills/figma-design-from-doc/references/doc-format.md),
with a fill-in template at
[templates/page-spec-template.docx](templates/page-spec-template.docx).

Google Docs `.docx` exports work, including the ones whose internal document part is
`word/document2.xml`. Legacy `.doc` does not — re-save as `.docx`.

## Requirements

- Claude Code with the Figma MCP server (shipped with this plugin)
- A Figma account with access to the component library. **A published library and a Figma
  team are not required** — with an unpublished library the design is built on a page
  inside the library file itself, where local components instance directly
- `python3` — a stock interpreter, nothing more. **No pip installs, no virtualenv, no
  pandoc.** Every script is standard library only.
  On macOS `python3` ships at `/usr/bin/python3` but needs Apple's Command Line Tools: if
  it isn't there, `xcode-select --install` takes a couple of minutes and is not Xcode. On
  Windows, install from python.org and use `python`. The skill checks for an interpreter
  up front and prints the fix rather than failing mid-run.

## Repository layout

```
DOC-FORMAT.md                       the authoring guideline to send colleagues
templates/
├── page-spec-template.docx         blank, fill it in
└── page-spec-example.docx          the same thing filled in
tools/make_doc_template.py          regenerates both templates
.claude-plugin/marketplace.json     this repo is its own marketplace
plugin/
├── .claude-plugin/plugin.json
├── .mcp.json                       Figma MCP server
├── config/defaults.json            team defaults: library key, desktop grid
└── skills/
    ├── figma-design-from-doc/      the pipeline
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── inference.md        content → design decisions (the design brain)
    │   │   ├── content-model.md    content.json schema
    │   │   ├── section-mapping.md  archetype → component mapping
    │   │   ├── desktop-conventions.md
    │   │   └── doc-format.md       optional markup reference
    │   └── scripts/
    │       ├── docx_extract.py     .docx → structured JSON (stdlib only)
    │       ├── analyze_content.py  sections + archetype proposals with reasons
    │       ├── check_doc.py        content readiness (--format for the markup)
    │       └── dgconfig.py         config layering + cache state
    └── figma-library-setup/        library picker
```

## Releasing an update

1. Make the change.
2. Bump `version` in **both** `.claude-plugin/marketplace.json` and
   `plugin/.claude-plugin/plugin.json` — they must agree or tagging refuses.
3. Commit and push to `main`.
4. `claude plugin tag ./plugin --push -m "%s"` to tag the release.
5. Teammates run `/plugin update figma-design-generator`.

**Which number to bump** — semver, read as *"can the same document now produce a different
design?"*

| | When |
|---|---|
| **major** | An installed project needs migration: config or library-map schema breaks, or a skill is renamed or removed |
| **minor** | The same input can produce a different design, or a new capability lands. Most changes, **including edits to the reference docs** — those files are the decision logic |
| **patch** | Nothing about the built design changes: wording, packaging, error text, a fix to a script that was outright failing |

`1.0.0` when the Figma build path is validated by people other than the author and the
config schemas have settled. Until then `0.x` minors may break things.

To set the team-wide default library, fill in `library` in `plugin/config/defaults.json`
before releasing. Until then, each person is asked once per project.

## Testing a change locally

```bash
# Extractor, against a real document
python3 plugin/skills/figma-design-from-doc/scripts/docx_extract.py \
  "/path/to/doc.docx" --out /tmp/out/content.json

# Format check
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py \
  templates/page-spec-example.docx        # should print "Clean", exit 0

# Config layering
python3 plugin/skills/figma-design-from-doc/scripts/dgconfig.py paths
python3 plugin/skills/figma-design-from-doc/scripts/dgconfig.py show
```

After editing the format spec, regenerate the templates so they don't drift:

```bash
python3 tools/make_doc_template.py
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py \
  templates/page-spec-example.docx
```

Install the working copy without pushing:

```
/plugin marketplace add /Users/you/Documents/GitHub/figma_design_generator_agent
/plugin install figma-design-generator
```
