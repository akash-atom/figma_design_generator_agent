# Writing docs this tool can design from

If you write page specs that get turned into Figma designs, this is the format to follow.

**→ [The format spec](plugin/skills/figma-design-from-doc/references/doc-format.md)** —
the full reference, with every label and what it maps to.

**→ [Blank template](templates/page-spec-template.docx)** — download, open in Word or
upload to Google Docs, fill it in.

**→ [Worked example](templates/page-spec-example.docx)** — the same thing filled in, so you
can see what "done" looks like.

## The short version

Structure lives in plain text labels. No special styling, no Word heading styles — the doc
stays a normal readable document.

```
Page: Employee self-service
URL slug: /solutions/employee-self-service

SECTION 1:
Layout: hero
Tag: Employee self-service
Heading: Delightful employee service, delivered autonomously
Description: Offer instant help round-the-clock across 5+ channels.
Button: Get a demo

SECTION 2:
Layout: feature-grid
Heading: Hire an AI Workforce to handle employee services
- Device Ops Engineer — Handles hardware support and device failures.
- Access Manager — Provisions application access across your SaaS stack.

SECTION 3:
Layout: cta-band
Heading: Ready to provide delightful employee service?
Button: Get a demo
```

Four things carry the whole format:

1. **`Page:`** once at the top. **`Heading:`** in every section.
2. **`SECTION 1:`, `SECTION 2:`** … mark where each page section starts.
3. **`Layout:`** names the section type — `hero`, `feature-grid`, `quote`, `cta-band` and
   six others. This is the single most useful line you can write: it's the difference
   between the design you pictured and a reasonable guess.
4. **`<angle brackets>`** on their own line name a component you want placed, like
   `<logo grid>`.

Anything you want the designer to read but not see goes in `Note:`. SEO fields
(`SEO title:`, `Meta description:`, `URL slug:`) are recognised as metadata and kept out of
the design.

Save as `.docx` — in Google Docs that's File → Download → Microsoft Word.

## Check your doc before sharing it

```bash
python3 plugin/skills/figma-design-from-doc/scripts/check_doc.py "My page.docx"
```

It tells you exactly what's missing and how to fix it. Needs nothing installed beyond
`python3`. Or just ask Claude Code to check the doc for you.

Blog posts and long-form articles don't need any of this — write them with normal Word or
Docs heading styles and they're read from those.
