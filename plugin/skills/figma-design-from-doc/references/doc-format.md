# Optional page spec markup

**None of this is required.** Write your content however you normally would and the design
is worked out from it — sections, layouts and components are all inferred (see
`inference.md`). Save as `.docx` and that is the whole requirement.

This format exists for when you *do* have a layout in mind and want to override those
choices. Use as much or as little of it as you like: a single `Layout:` line on one
section is a perfectly good way to use this page.

Structure is carried in plain text labels, so the doc stays readable as a document. No
special styling is needed.

Check a doc before handing it over:

```bash
python3 scripts/check_doc.py "My page.docx"            # is there enough content?
python3 scripts/check_doc.py "My page.docx" --format   # is the optional markup valid?
```

---

## Shape

```
Page: Employee self-service
URL slug: /solutions/employee-self-service
SEO title: Employee self-service software | Atomicwork
Meta description: Give employees instant answers across Slack, Teams and email.

SECTION 1:
Layout: hero
Tag: Employee self-service
Heading: Delightful employee service, delivered autonomously
Description: Offer instant help round-the-clock for your employees through 5+ channels.
Button: Get a demo
Button 2: Take the tour

SECTION 2:
Layout: logo-band
Heading: Trusted by service teams everywhere
<logo grid>

SECTION 3:
Layout: feature-grid
Heading: Hire an AI Workforce to handle employee services
Description: Offload access automation, troubleshooting and policy questions.
- Device Ops Engineer — Handles hardware support, device failures and peripherals.
- Access Manager — Provisions and de-provisions application access across SaaS.
- HR Ops Specialist — Answers everyday HR requests, onboarding and policy questions.

SECTION 4:
Layout: quote
Quote: Atomicwork cut our resolution time from days to minutes.
Author: Jane Doe
Role: Head of IT, Zuora

SECTION 5:
Layout: cta-band
Heading: Ready to provide delightful employee service?
Button: Get a demo
```

---

## Page header

Goes once, above `SECTION 1`.

| Label | Required | Purpose |
|---|---|---|
| `Page:` | **yes** | Names the Figma frame. Keep it short — `Employee self-service`, not `[Website] Solutions - Employee self-service v3 FINAL` |
| `URL slug:` | no | Metadata. **Not rendered.** |
| `SEO title:` | no | Metadata. **Not rendered.** |
| `Meta description:` | no | Metadata. **Not rendered.** |
| `Template:` `Owner:` `Status:` `Reviewer:` | no | Metadata. **Not rendered.** |

Everything in this block is excluded from the design except `Page:`.

## Sections

Each section starts with a line of its own:

```
SECTION 3:
```

`SECTION 3: Feature grid` also works — the trailing name is used as a fallback heading.
Numbering must ascend, but gaps are fine; the order in the document is what determines
the order on the page.

### `Layout:` — the most useful line you can write

One of these keywords. It picks the component directly, so you get what you intended
rather than what the content happened to look like:

| `Layout:` | What you get |
|---|---|
| `hero` | Full-width opening section: eyebrow, big heading, body, one or two CTAs |
| `logo-band` | A strip of customer logos |
| `feature-grid` | 3–6 cards in a grid |
| `feature-split` | Heading and body on one side, image on the other |
| `stat-band` | A row of numbers with labels |
| `quote` | Testimonial with attribution |
| `accordion` | Expandable list, good for FAQs |
| `table` | A comparison or spec table |
| `cta-band` | Closing call to action |
| `footer` | Page footer |

Spelling is forgiving — `Feature Grid`, `feature grid` and `feature-grid` all work. An
unrecognised value is flagged by the linter rather than silently guessed at.

Omit `Layout:` and the archetype is inferred from the content shape. That usually works,
but it is a guess.

### Section labels

| Label | Maps to | Notes |
|---|---|---|
| `Heading:` | the section headline | Overrides the inferred headline |
| `Tag:` | eyebrow / pill above the heading | Also `Eyebrow:`, `Kicker:` |
| `Subheading:` | subtitle under the heading | |
| `Description:` | body copy | Also `Body:`, `Copy:` |
| `Button:` | primary CTA label | |
| `Button 2:` | secondary CTA label | Also `Secondary button:` |
| `Link:` | a text link | Put the URL after the colon or link the text |
| `Quote:` | testimonial copy | |
| `Author:` | who said it | Add `Role:` for their title and company |
| `Stat:` | a single metric | One `Stat:` line per number |
| `Caption:` | image caption | |
| `Note:` | instruction to the designer | **Never rendered.** Use for anything you want read but not shown |

One label per line, label first, colon, then the value. Repeat a label only where the
table above says you can (`Stat:`, `Button`/`Button 2:`).

### Repeated items — use a bulleted list

For the cards in a `feature-grid`, the rows in a `stat-band`, or the entries in an
`accordion`, use the document's own bullet list and separate each item's title from its
body with an em dash or a hyphen:

```
- Device Ops Engineer — Handles hardware support, device failures and peripherals.
- Access Manager — Provisions and de-provisions application access across SaaS.
```

Title-only items are fine too. Keep every item in one section to the same shape — three
items with bodies and two without will produce an uneven grid.

### `<Angle brackets>` — name a component or visual

A line wrapped in angle brackets names something you want placed, and is matched against
the component library by name:

```
<logo grid>
<coworker grid>
<zuora testimonial block>
<product screenshot>
```

This is how you ask for a specific component. If the library has no match, the build
reports it as a gap instead of substituting something that merely looks close. Trailing
text after the closing bracket is kept as a note:

```
<product screenshot> use the latest dashboard capture from the launch deck
```

### Images

Paste images straight into the document. They're extracted at their displayed size. Add
`Caption:` for a caption, and use the image's own alt text in Word/Docs if you want it
carried through.

Linked images (inserted by URL rather than pasted) cannot be pulled into Figma — paste the
image itself.

---

## Rules that matter

These apply *if* you use the markup. Without it, none of them do.

1. **`Page:` once at the top** names the Figma frame. Otherwise the document title is used.
2. **One `SECTION n:` per page section.** Don't stack two sections' worth of content under
   one marker; the layout has no way to split them.
3. **`Layout:` wherever you know what you want.** It is the difference between the design
   you pictured and a reasonable guess.
4. **Put instructions in `Note:`, not in prose.** A sentence like "this bit should be on
   the left" sitting in the body copy will be rendered as body copy. `Note: media on the
   left` will not.
5. **Don't number or letter your own headings.** `Heading: 1. Get started` puts the "1." in
   the design.
6. **Write final copy, not placeholders.** `Heading: TBD` builds a design that says TBD.
   This is the one rule that matters whether or not you use the markup.
7. **Save as `.docx`.** Google Docs → File → Download → Microsoft Word. Legacy `.doc` is
   not supported.

## Long-form documents

Blog posts and articles need none of this, and shouldn't use it. Write them with normal
heading styles — or with nothing at all — and they are detected as long-form and laid out
as an article: a title and a single column of copy, rather than a page of bands.
