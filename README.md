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

## Document conventions it understands

It reads both kinds of document:

**Page specs** that carry structure in plain text — the Atomicwork website-doc convention:

```
Tag: Employee self-service
SECTION 1:
Heading: Delightful employee service, delivered autonomously
Description: Offer instant help round-the-clock…
<logo grid>
Button: Get a demo
```

`SECTION n:` splits sections. `Label:` lines assign a role (`Tag`, `Heading`,
`Description`, `Button`, `Quote`, `Stat`, …). `<angle brackets>` name the component or
visual you want — these are matched against your library by name. `SEO title:` and
`Meta description:` are recognised as metadata and kept out of the design.

**Long-form docs** that use real Word heading styles — H1 becomes the hero, each H2 a
section.

Google Docs `.docx` exports work, including the ones whose internal document part is
`word/document2.xml`. Legacy `.doc` does not — re-save as `.docx`.

## Requirements

- Claude Code with the Figma MCP server (shipped with this plugin)
- A Figma account with access to the component library, on a plan that allows file creation
- `python3` — stock macOS/Linux Python is fine. **No pip installs, no pandoc.** The `.docx`
  extractor is standard library only, so it works on a teammate's machine with no setup.

## Repository layout

```
.claude-plugin/marketplace.json     this repo is its own marketplace
plugin/
├── .claude-plugin/plugin.json
├── .mcp.json                       Figma MCP server
├── config/defaults.json            team defaults: library key, desktop grid
└── skills/
    ├── figma-design-from-doc/      the pipeline
    │   ├── SKILL.md
    │   ├── references/             content schema, archetype mapping, layout conventions
    │   └── scripts/
    │       ├── docx_extract.py     .docx → structured JSON (stdlib only)
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

# Config layering
python3 plugin/skills/figma-design-from-doc/scripts/dgconfig.py paths
python3 plugin/skills/figma-design-from-doc/scripts/dgconfig.py show
```

Install the working copy without pushing:

```
/plugin marketplace add /Users/you/Documents/GitHub/figma_design_generator_agent
/plugin install figma-design-generator
```
