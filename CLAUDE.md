# CLAUDE.md — figma_design_generator_agent

## What this is

A **Claude Code plugin** (and its own marketplace) that generates desktop Figma designs
from Word documents using a pinned Figma component library. It is not a Webflow project —
the workspace-level `~/Documents/GitHub/CLAUDE.md` archetypes do not apply here.

Distribution: this repo is both the plugin and the marketplace. Teammates run
`/plugin marketplace add akash-atom/figma_design_generator_agent` then
`/plugin install figma-design-generator`, and get updates with `/plugin update`.

## Architecture

The plugin is a **thin orchestrator over the Figma MCP server's own skills**. Those ship as
MCP resources, not files — read them with `ReadMcpResourceTool` on server
`figma-remote-mcp`:

- `skill://figma/figma-use/SKILL.md` — mandatory before any `use_figma` call
- `skill://figma/figma-generate-design/SKILL.md` — the section-by-section assembly workflow
- `skill://figma/figma-create-new-file/SKILL.md` — mandatory before `create_new_file`

When calling `use_figma`, pass `skillNames: "resource:figma-use,resource:figma-generate-design"`.

**Do not reimplement** design-system discovery, wrapper-frame creation, variable binding or
screenshot validation — those skills already do it. This plugin owns only the four things
they don't: library pinning, `.docx` → content model, the reviewable section plan, and team
distribution.

## Hard constraints

- **`scripts/*.py` must stay Python 3 standard library only.** No pip, no pandoc, no
  LibreOffice. Teammates run these on stock `python3` with zero setup; neither
  `python-docx` nor `pandoc` is installed on the maintainer's machine either. If you reach
  for a dependency, you have taken a wrong turn.
- **Skill frontmatter is `name` + `description` only**, matching the convention across this
  user's other skills. Don't add `allowed-tools`.
- The `.docx` main document part is **not always `word/document.xml`** — Google Docs
  exports use `word/document2.xml`. Resolve it through `_rels/.rels`. This is covered by a
  test document; don't regress it.
- `search_design_system` rejects speculative synonym sweeps. Query terms must be derived
  from the document's actual needs, and always scoped with `includeLibraryKeys`.

## The page spec format

`plugin/skills/figma-design-from-doc/references/doc-format.md` is the **canonical** format
spec. Root `DOC-FORMAT.md` is a short pointer for colleagues — keep it a pointer, never a
second copy of the spec (the `webflow-design-system.md` / synced-skill pair in this user's
setup is the drift this avoids).

`templates/*.docx` are **generated**, not hand-edited. After changing the format:

```bash
python3 tools/make_doc_template.py
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py \
  templates/page-spec-example.docx   # must print "Clean", exit 0
```

The worked example passing the linter cleanly is the regression test for the whole format
chain: spec -> template -> example -> extractor -> linter.

Three places must stay in sync when adding an archetype or a label:

1. `LABEL_ROLES` / `LAYOUTS` in `scripts/docx_extract.py`
2. `references/doc-format.md` (the label and layout tables)
3. `references/section-mapping.md` (how the archetype maps to a component)

Per-layout checks live in `check_doc.py` -> `check_section`.

## Config layering

Highest priority first:

1. `./.figma-design/config.json` — per project, written by `dgconfig.py set`
2. `~/.claude/figma-design-generator/config.json` — per user
3. `plugin/config/defaults.json` — shipped team defaults

`dgconfig.py show` prints the merged result plus which layer each value came from.

## Releasing

Bump `version` in **both** `.claude-plugin/marketplace.json` and
`plugin/.claude-plugin/plugin.json`, then commit and push. Don't push or publish unless
asked — it changes what teammates receive.

## Testing

Real documents to test the extractor against (all in `~/Downloads`, not in the repo):

- `[Website] Solutions - Employee self-service.docx` — `section-markers` structure, the
  `SECTION n:` / `Heading:` / `<logo grid>` convention, 4 embedded images
- `[Feature page] AI coworkers library.docx` — main part is `word/document2.xml`, 76
  placeholders, one table
- `AI workforce.docx` — `headings` structure, clean H1/H2 nesting
- `Events Roundup Blogpost 2026.docx` — `headings`, H2-only

Write test output to the scratchpad, never into the repo. `.figma-design/` is gitignored —
it is per-project run state, not source.
