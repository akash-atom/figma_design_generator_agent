# Desktop layout conventions

Values come from `config.desktop` (see `plugin/config/defaults.json`); the numbers below
are the shipped defaults. A project can override them in `.figma-design/config.json`.

| Key | Default | Meaning |
|---|---|---|
| `frameWidth` | 1440 | Wrapper frame width — the standard desktop artboard |
| `contentMaxWidth` | 1200 | Inner content column; sections fill 1440, content caps at 1200 |
| `sectionPaddingY` | 120 | Vertical padding inside each section |
| `sectionPaddingX` | 120 | Horizontal padding — gives the 1200 content column inside 1440 |
| `gridColumns` | 12 | Column count for grid sections |
| `gridGutter` | 24 | Gap between grid columns |
| `sectionNamePrefix` | `Section / ` | Frame naming prefix |

**Prefer the library's own spacing variables over these numbers.** They are the fallback
for when the design system exposes no spacing token — bind `setBoundVariable("paddingTop", …)`
whenever a token exists.

## Structure

```
<Document title>                 1440 wide, VERTICAL auto-layout, HUG height, gap 0
├── Section / Hero               FILL width, HUG height, padding 120/120
│   └── Content                  1200 wide max, VERTICAL, centred
├── Section / Logo Band
├── Section / Feature Grid
│   └── Content                  HORIZONTAL wrap, gap 24
└── Section / CTA
```

- The wrapper is created in **its own** `use_figma` call and its ID is returned. Every
  section is appended straight into it. Never build sections at page level and reparent —
  `appendChild` across calls silently fails and orphans frames.
- Each section is a full-bleed `FILL`-width auto-layout frame so its background colour runs
  edge to edge; the 1200px content frame sits centred inside it.
- Set `layoutSizingHorizontal = "FILL"` **after** appending the child, never before.
- Wrapper height is HUG. Do not set an explicit page height.

## Naming

- Wrapper: the document title, cleaned of spec noise — `[Website] Solutions - Employee
  self-service` becomes `Employee self-service`.
- Sections: `Section / Hero`, `Section / Feature Grid`. Where the doc used numbered
  markers, keep the order but name by content, not `Section / 4`.
- Content frames: `Content`. Grid wrappers: `Grid`. Rows: `Row`.

## Section rhythm

- Alternate section background fills (surface/default → surface/subtle) so sections read as
  distinct bands. Use the library's semantic surface variables, never hex.
- Keep `sectionPaddingY` uniform. Vary emphasis with type scale and background, not with
  ad-hoc padding.
- Hero may take more vertical padding than the rest (1.5× is a reasonable ceiling).

## Consistency across sections

These are page-level and easy to miss when sections are built one call at a time. Decide
each once, up front, and apply it to every section.

**Header alignment.** If the library's section header exposes a left/centre property,
pick one for the page and keep it. Left-aligned headers with one centred section in the
middle reads as a mistake, not as emphasis. Centre the hero if the library's hero does;
left-align the rest.

**Background rhythm.** Alternate surfaces deliberately rather than per section as you
build. Four consecutive light sections at the top of a page is the common outcome of
deciding one at a time — decide the whole sequence before the first build call, and write
it into the plan.

**Section padding.** Take the padding from the library's own section components where
they set it. Only fall back to `config.desktop` values for sections you build by hand,
and use the same value throughout so bands don't drift.

## Placeholders should be the size of the real thing

When a component is missing or an image can't be placed, the placeholder frame stands in
for real content — so size it like the content it replaces, not like the space left over.
A 560px dashed box for a missing grid leaves a hole that dominates the page and distorts
every judgement about rhythm around it.

Estimate from what the content implies: a grid of six cards is roughly two rows of ~280px,
a product screenshot is roughly 16:9 at the content width. Label it with what is missing
and why, as the build already does.

The same applies to a section whose copy arrived thin. A hero with a headline, one line of
body and a button does not need 520px of band — let it hug, with the library's own
vertical padding. Empty space that was not designed reads as a bug.

## Typography and colour

- Text styles come from the library (`node.textStyleId`), never from manual font size and
  weight. If the library has no text style for something, use the closest one rather than
  inventing a size.
- Resolve the product font from the library's own text styles. Do **not** default to Inter.
  If you do load Inter, note that Figma spells the styles `Semi Bold` and `Extra Bold`, with
  the space.
- All fills bind to colour variables via `setBoundVariableForPaint`.

## Images

`use_figma` cannot fetch an external image URL. For each image the extractor pulled into
`.figma-design/assets/`, either:

1. `upload_assets` it and set the returned hash as an `IMAGE` fill, or
2. create a placeholder frame at the image's `widthPx` × `heightPx`, filled with a subtle
   surface variable and labelled with the image's `alt` text or filename.

State which one you did, per image, in the plan and in the final report.
