# Writing content for design generation

**Just write the content.** You don't need to think about layout, sections, components or
formatting — the tool reads what you wrote and makes the design decisions.

There is no format to learn. Write the page the way you'd write it for a colleague, save
it as `.docx`, and hand it over.

## What actually helps

Not formatting rules — just the things that make a page work:

1. **A line at the top of each part naming what it's about.** It doesn't need to be styled
   as a heading. "Hire an AI Workforce to handle employee services" on its own line is
   enough to become that section's headline.
2. **Write sets as sets.** If three things belong together, write them in the same shape —
   three bullets, or three short paragraphs that each start with the thing's name. Even
   lengths matter more than you'd think: three items of 15 words and two of 60 can't be
   laid out as one tidy row.
3. **Put the numbers in.** "65% of requests resolved without a human" gets pulled out as a
   headline statistic. "Most requests" doesn't.
4. **End with the ask.** "Get a demo", "Start a trial" — one short line. **If you don't
   write one, no button is added.** Nothing gets invented on your behalf.
5. **Paste images in**, don't insert them by URL. A linked image can't be pulled into
   Figma.
6. **Final copy, not placeholders.** `TBD` gets built into the design as `TBD`.

That's it. Everything else is the designer's job, and the designer here is the tool.

## What it works out for you

- Where the sections start and end, even if you never used a heading.
- What each section should be — an opening banner, a row of cards, a statistic strip, a
  quote, a closing call to action.
- When a section is really two, and splits it.
- When a run of paragraphs you wrote as prose is actually a set of cards.
- Which component from the design library fits, and which copy goes in which slot.
- When your document isn't a page at all but a blog post, and lays it out as an article
  instead.

You'll get a plan showing every decision and why, before anything is built. Change
anything you disagree with.

## Two promises about your words

**Your copy is never rewritten to fit the design.** If a paragraph is too long for the
component that would otherwise suit it, the tool uses a component that fits, or lays it
out at the length you wrote it. If something genuinely has to be cut, you're shown the
exact before and after and asked first.

**Nothing is invented.** No filler headlines, no "Learn more" buttons you didn't write, no
eyebrow labels conjured up to fill a slot. If the copy isn't there, the slot stays empty
and you're told.

## Check a doc before handing it over

```bash
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py "My page.docx"
```

It only reports things you can act on: not enough content, a section with no opening line,
placeholder text, a paragraph too long to lay out, a linked image. It says nothing about
layout. Or just ask Claude Code to check it.

## If you *do* have a layout in mind

Optional — for when you know you want a specific treatment and would rather say so than
have it inferred. Add a `Layout:` line to any section:

```
SECTION 3:
Layout: feature-grid
Heading: Hire an AI Workforce to handle employee services
- Device Ops Engineer — Handles hardware support and device failures.
- Access Manager — Provisions application access across your SaaS stack.
```

Values: `hero`, `logo-band`, `feature-grid`, `feature-split`, `stat-band`, `quote`,
`accordion`, `table`, `cta-band`, `footer`. You can also name a component directly on its
own line, like `<logo grid>`.

Use it on one section or none. The
**[full markup reference](plugin/skills/figma-design-from-doc/references/doc-format.md)**
has every label, and
**[templates/page-spec-template.docx](templates/page-spec-template.docx)** is a
fill-in-the-blanks version if you'd rather work that way. Neither is required.
