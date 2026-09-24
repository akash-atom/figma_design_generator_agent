---
name: figma-library-setup
description: "Pin, inspect or change the Figma component library that figma-design-from-doc builds with. Use when the user wants to choose or switch the Figma component library or design system for design generation, when no library is configured yet, when they ask which library is pinned, or when they want to point a project at a different design system."
---

# Pin a Figma component library

One-time setup per project. Writes the chosen library into
`./.figma-design/config.json` so `figma-design-from-doc` never has to ask again.

Scripts are at `$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/`. Resolve the
interpreter first with `PY=$(command -v python3 || command -v python)`; if neither is
found, see the prerequisites in `figma-design-from-doc`'s SKILL.md — on macOS the fix is
`xcode-select --install`.

## Step 1 — Show what is currently pinned

```bash
"$PY" "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/dgconfig.py" show
"$PY" "$CLAUDE_PLUGIN_ROOT/skills/figma-design-from-doc/scripts/dgconfig.py" paths
```

If a library is already pinned and the user only asked *which* one, report it with its
provenance layer (`project` / `user` / `plugin`) and stop. Don't re-run setup unasked.

## Step 2 — Get a file key to query against

`get_libraries` needs a `fileKey`. In priority order:

1. `targetFileKey` from the config.
2. A `https://figma.com/design/<fileKey>/...` URL the user pastes — this can be the design
   file they intend to build in, **or** the library file itself.
3. If they have neither, read `skill://figma/figma-create-new-file/SKILL.md` via
   `ReadMcpResourceTool`, call `whoami` for the `planKey`, and `create_new_file`. A blank
   file still lists the whole organisation's available libraries.

## Step 3 — List the libraries

```
get_libraries({ fileKey: "<FILEKEY>" })
```

Two lists come back:

- `libraries_added_to_file` — already subscribed. **Prefer these**: components import
  without the user having to add the library first.
- `libraries_available_to_add` — community UI kits plus organisation libraries.

Organisation libraries are paginated 20 at a time. When
`libraries_available_to_add_next_offset` is non-null and the library the user named isn't
on the page yet, call `get_libraries` again with that `offset`. Page through before
concluding a library doesn't exist — community kits only appear on the first page.

## Step 4 — Let the user choose

Present the candidates with AskUserQuestion — name plus source type, subscribed ones
first. If the user already named a library in their message and exactly one entry matches,
pick it and just confirm the choice in one line.

## Step 5 — Save

```bash
"$PY" .../dgconfig.py set \
  --library-key "<libraryKey>" \
  --library-name "<name>" \
  --library-file-key "<library's own fileKey, if known>" \
  --scope project
```

Use `--scope user` instead when the user wants this library as their personal default
across all projects.

**Always capture `--library-file-key`** — the file key of the library file itself, from
its own `figma.com/design/<fileKey>/...` URL. It is not optional in practice: with it,
`figma-design-from-doc` reads the components straight out of the library file, which is
exact and complete. Without it, discovery falls back to name-matching against
`search_design_system`. Ask the user for the library file's URL if you don't already have
it.

## Step 6 — Pick the mode

Ask whether the library is **published**. This decides how components are referenced, and
an unpublished library is not a blocker:

- **Published** → `--mode published`. Components are imported by key into any file. This
  is what you want once the library is shared with the team.
- **Not published** (no team yet, personal draft, work in progress) → `--mode local`, and
  set `targetFileKey` to the library's own file key. Designs are built on a new page
  **inside the library file**, where local components instance directly by node id.
  Variables and text styles resolve locally too. Nothing needs publishing, and the result
  is real component instances, not hand-built frames.

Local mode is a complete path, not a degraded one. The only thing it gives up is building
into a separate file. When the library is published later, re-run this skill with
`--mode published` and a real target file; the component map rediscovers with keys.

```bash
"$PY" .../dgconfig.py set --mode local --file-key "<library file key>"
```

Confirm with `dgconfig.py show`, which prints the resolved mode and what it implies.

Changing the library invalidates any cached component map. Tell the user that the next
design run will rediscover components — `dgconfig.py cache-status` reports `STALE` and
`figma-design-from-doc` handles it automatically.

## Setting the team-wide default

To make a library the default for everyone who installs this plugin, put its key in
`$CLAUDE_PLUGIN_ROOT/config/defaults.json` under `library`, bump `version` in both
`.claude-plugin/marketplace.json` and `plugin/.claude-plugin/plugin.json`, then commit and
push. Teammates pick it up with `/plugin update`. Only do this when the user explicitly
asks for a team default — it is a change to shared, published configuration.
