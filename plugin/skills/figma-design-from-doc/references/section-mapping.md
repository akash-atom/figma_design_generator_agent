# Choosing a section archetype

For each section in `content.json`, pick one archetype, then find the library component
that serves it. Resolve in this order — stop at the first rule that fires.

## 1. The placeholder wins

If the section has a `placeholders` entry, it names what the author wants. Match it against
`library-map.json` component names, tolerating word order and plurals:

| Placeholder in the doc | Search the library for |
|---|---|
| `<logo grid>`, `<logo band>`, `<logo cloud>` | logo wall / logo strip / customer logos |
| `<coworker grid>`, `<feature grid>`, `<card grid>` | card grid / feature grid / tile grid |
| `<zuora testimonial block>`, `<quote>` | testimonial / quote card |
| `<Atom grid>`, `<product screenshot>` | image frame / media block |
| `<accordion>`, `<FAQ>` | accordion / FAQ list |
| `<stats>`, `<metrics>` | stat band / metric row |
| `<CTA banner>` | CTA band / call-to-action section |

A named brand inside a placeholder (`<zuora testimonial block>`) is *content*, not part of
the component name — search for "testimonial", then fill Zuora's details from the section's
copy. If the copy isn't in the doc, leave the component's own placeholder text and flag it.

If nothing in the library matches as a whole section, **compose one** from the library's
molecules — a container frame you build, filled with `Heading Block`, `Card`, `Icon Row`
instances. Record the composition in the plan ("Grid frame + Heading Block + 3 × Card")
rather than calling it a manual build; the pieces are still real instances. Record a
genuine gap in `library-map.json` → `unmatched`. **Do not substitute a component that merely looks
close** — a detached approximation is worse than an honest gap.

## 2. The analyser's proposal

`analysis.json` already ranked the archetypes with reasons. Take its top candidate at
`high` confidence. At `medium` or `low`, weigh it against what the library actually has —
a scored `feature-grid` is worthless if the library has no grid component.

## 3. Position in the document

- **First section** with a heading + body + CTA → `hero`.
- **Last section** with a CTA and little else → `cta-band`, then `footer` if the library
  has one.
- A section immediately after the hero holding only logos or a logo placeholder →
  `logo-band`.

## 4. Content shape

| Shape in the section | Archetype |
|---|---|
| eyebrow + heading + body + one or two CTAs | `hero` |
| heading + body + a list of 3–6 short items | `feature-grid` |
| heading + body + one image | `feature-split` |
| a list of 2–4 items that are mostly numbers/percentages | `stat-band` |
| `quote` role, or a long paragraph with an `attribution` | `quote` |
| a list of 5+ items with long bodies, or Q/A pairs | `accordion` |
| a `table` block | `table` |
| heading + `cta` role only | `cta-band` |
| headings with nested subsections | one section per subsection, not one giant section |

## 5. Content mapping rules

Once the component is chosen, map roles to its TEXT properties using the `properties` map
in `library-map.json`:

| Role | Goes to |
|---|---|
| `eyebrow` | the eyebrow/tag/kicker property, or the component's badge slot |
| `heading` | the heading/title property |
| `subheading` | the subtitle property if one exists, else the body property |
| `body` | the body/description property |
| `cta` | the nested Button's label property — call `setProperties()` on the *nested* instance |
| `link` | the Button's or Link's href, as an interaction or a plain text URL |
| `quote` | the quote property |
| `attribution` | the author/name property; a trailing `", Title, Company"` splits into the role/company properties when they exist |
| `stat` / `metric` | the value property; the words around it go to the label property |
| `caption` | the image caption property |

When a section has no `roles` at all (plain prose, no labels), infer: first line →
heading, following paragraph → body, a trailing short imperative sentence → CTA.

**For repeated items, build the full content array before touching Figma.** Split each
list item (or each parallel paragraph) on its first `.`, `—` or `:` into title and body,
and lay the array out in the plan so the user can see all of it. Then create exactly one
instance per entry. The failure to watch for is a grid where every card carries the first
item's copy — it renders cleanly and reads as finished until you actually read it.

**Never render** `role: "note"` (author instructions) or `role: "meta"` (SEO fields) as
visible copy. Notes are layout direction — "On the left: ServiceNow and JSM logos" means
choose the left-aligned variant and put those logos there.

## 6. Variant selection

Prefer the variant the content justifies over the component's default:

- Two CTAs → the variant with a secondary button, not two primaries.
- An image mentioned as "on the right" → the right-media variant.
- Section 1 → the largest size variant available; mid-page sections → the default size.
- Alternate `feature-split` media side down the page if the library exposes a side
  property; a page of six identical left-media splits reads as a mistake.

Record the variant you chose in the plan table so the user can correct it before the build.
