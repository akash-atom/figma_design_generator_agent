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
4. **Plan** — a section-by-section table of which component and variant fills each section,
   and which text goes where. **You approve this before anything is written to Figma.**
5. **Build** — a 1440px frame of real library component instances, with colours and spacing
   bound to library variables.
6. **Validate** — one screenshot pass for clipped text, wrong variants, leftover
   placeholders and the wrong font.

## The document format

**Writing the docs? Read [DOC-FORMAT.md](DOC-FORMAT.md)** — that's the page you send
colleagues. Start from [templates/page-spec-template.docx](templates/page-spec-template.docx),
or see [templates/page-spec-example.docx](templates/page-spec-example.docx) filled in.

In short: structure lives in plain text labels, so the doc stays readable as a document.

```
Page: Employee self-service

SECTION 1:
Layout: hero
Tag: Employee self-service
Heading: Delightful employee service, delivered autonomously
Description: Offer instant help round-the-clock…
Button: Get a demo
<logo grid>
```

`SECTION n:` splits sections. `Layout:` names the archetype (`hero`, `feature-grid`,
`quote`, `cta-band`, …) and is the strongest signal you can give. `Label:` lines assign a
role (`Tag`, `Heading`, `Description`, `Button`, `Quote`, `Stat`, `Note`, …). `<angle
brackets>` name a component, matched against your library. `SEO title:`/`Meta description:`
are treated as metadata and kept out of the design.

Check a doc before generating from it:

```bash
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py "My page.docx"
```

It reports what's missing and how to fix it, and exits 1 on errors so it can gate a
workflow. The skill runs it automatically.

**Long-form docs** (blog posts, articles) need none of this — use real Word heading styles
and structure is read from those. H1 becomes the hero, each H2 a section.

Google Docs `.docx` exports work, including the ones whose internal document part is
`word/document2.xml`. Legacy `.doc` does not — re-save as `.docx`.

## Requirements

- Claude Code with the Figma MCP server (shipped with this plugin)
- A Figma account with access to the component library, on a plan that allows file creation
- `python3` — stock macOS/Linux Python is fine. **No pip installs, no pandoc.** The `.docx`
  extractor is standard library only, so it works on a teammate's machine with no setup.

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
    │   │   ├── doc-format.md       canonical page spec format
    │   │   ├── content-model.md    content.json schema
    │   │   ├── section-mapping.md  archetype selection rules
    │   │   └── desktop-conventions.md
    │   └── scripts/
    │       ├── docx_extract.py     .docx → structured JSON (stdlib only)
    │       ├── check_doc.py        lints a doc against the format
    │       └── dgconfig.py         config layering + cache state
    └── figma-library-setup/        library picker
```

## Releasing an update

1. Make the change.
2. Bump `version` in **both** `.claude-plugin/marketplace.json` and
   `plugin/.claude-plugin/plugin.json`.
3. Commit and push to `main`.
4. Teammates run `/plugin update figma-design-generator`.

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
