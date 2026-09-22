#!/usr/bin/env python3
"""Generate templates/page-spec-template.docx from the format spec.

Standard library only -- writes the OOXML by hand so the template stays
reproducible and reviewable in git. Run this after editing the format spec:

    python3 tools/make_doc_template.py

The generated bullets are real Word list items (w:numPr), not typed dashes,
because the page spec format relies on list structure for grid and accordion
items.
"""

import os
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_OUT = os.path.join(REPO, "templates", "page-spec-template.docx")
EXAMPLE_OUT = os.path.join(REPO, "templates", "page-spec-example.docx")
FIXED_DATE = (2026, 1, 1, 0, 0, 0)

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/>
</w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>
<w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>
<w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/>
<w:basedOn w:val="Normal"/><w:pPr><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
</w:styles>"""

NUMBERING = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:abstractNum w:abstractNumId="0">
<w:lvl w:ilvl="0"><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/>
<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))


def para(text="", bold=False, style=None, bullet=False, italic=False):
    ppr = ""
    if bullet:
        ppr = ('<w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr>'
               '<w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>')
    elif style:
        ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style
    if not text:
        return "<w:p>%s</w:p>" % ppr
    rpr = ""
    if bold or italic:
        rpr = "<w:rPr>%s%s</w:rPr>" % ("<w:b/>" if bold else "",
                                       "<w:i/>" if italic else "")
    return ('<w:p>%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            % (ppr, rpr, esc(text)))


def build_body():
    p = []
    a = p.append

    a(para("How to use this template", bold=True))
    a(para("Replace every value after a colon with your own copy, then delete "
           "any label you don't need. Delete this instruction block before "
           "handing the doc over.", italic=True))
    a(para("Check your doc before sharing it: run check_doc.py, or ask Claude "
           "Code to check it.", italic=True))
    a(para())
    a(para("Labels: Layout, Tag, Heading, Subheading, Description, Button, "
           "Button 2, Link, Quote, Author, Role, Stat, Caption, Note.",
           italic=True))
    a(para("Layout values: hero, logo-band, feature-grid, feature-split, "
           "stat-band, quote, accordion, table, cta-band, footer.",
           italic=True))
    a(para("Use <angle brackets> on a line of its own to name a component you "
           "want, e.g. <logo grid>.", italic=True))
    a(para())
    a(para("--- delete everything above this line ---", italic=True))
    a(para())

    # Page header
    a(para("Page: "))
    a(para("URL slug: "))
    a(para("SEO title: "))
    a(para("Meta description: "))
    a(para())

    # Section 1 - hero
    a(para("SECTION 1:"))
    a(para("Layout: hero"))
    a(para("Tag: "))
    a(para("Heading: "))
    a(para("Description: "))
    a(para("Button: "))
    a(para("Button 2: "))
    a(para())

    # Section 2 - logo band
    a(para("SECTION 2:"))
    a(para("Layout: logo-band"))
    a(para("Heading: "))
    a(para("<logo grid>"))
    a(para())

    # Section 3 - feature grid
    a(para("SECTION 3:"))
    a(para("Layout: feature-grid"))
    a(para("Heading: "))
    a(para("Description: "))
    a(para("Card title one — what it does, in a sentence.", bullet=True))
    a(para("Card title two — what it does, in a sentence.", bullet=True))
    a(para("Card title three — what it does, in a sentence.", bullet=True))
    a(para())

    # Section 4 - feature split
    a(para("SECTION 4:"))
    a(para("Layout: feature-split"))
    a(para("Heading: "))
    a(para("Description: "))
    a(para("Note: media on the right"))
    a(para("<product screenshot>"))
    a(para())

    # Section 5 - quote
    a(para("SECTION 5:"))
    a(para("Layout: quote"))
    a(para("Quote: "))
    a(para("Author: "))
    a(para("Role: "))
    a(para())

    # Section 6 - stat band
    a(para("SECTION 6:"))
    a(para("Layout: stat-band"))
    a(para("Heading: "))
    a(para("Stat: "))
    a(para("Stat: "))
    a(para("Stat: "))
    a(para())

    # Section 7 - cta band
    a(para("SECTION 7:"))
    a(para("Layout: cta-band"))
    a(para("Heading: "))
    a(para("Description: "))
    a(para("Button: "))
    return "".join(p)


def build_example():
    """A filled-in page spec that passes check_doc.py cleanly."""
    p = []
    a = p.append

    a(para("Page: Employee self-service"))
    a(para("URL slug: /solutions/employee-self-service"))
    a(para("SEO title: Employee self-service software | Atomicwork"))
    a(para("Meta description: Give employees instant answers across Slack, "
           "Teams and email, without adding headcount."))
    a(para())

    a(para("SECTION 1:"))
    a(para("Layout: hero"))
    a(para("Tag: Employee self-service"))
    a(para("Heading: Delightful employee service, delivered autonomously"))
    a(para("Description: Offer instant help round-the-clock for your "
           "employees across 5+ channels, with an AI workforce that resolves "
           "requests end to end."))
    a(para("Button: Get a demo"))
    a(para("Button 2: Take the tour"))
    a(para())

    a(para("SECTION 2:"))
    a(para("Layout: logo-band"))
    a(para("<logo grid>"))
    a(para())

    a(para("SECTION 3:"))
    a(para("Layout: feature-grid"))
    a(para("Heading: Hire an AI Workforce to handle employee services"))
    a(para("Description: Offload access automation, troubleshooting and "
           "policy questions to coworkers that own the outcome."))
    a(para("Device Ops Engineer — Handles hardware support, device "
           "failures and peripheral requests.", bullet=True))
    a(para("Access Manager — Provisions and de-provisions application "
           "access across your SaaS stack.", bullet=True))
    a(para("HR Ops Specialist — Answers everyday HR requests, "
           "onboarding steps and policy questions.", bullet=True))
    a(para())

    a(para("SECTION 4:"))
    a(para("Layout: feature-split"))
    a(para("Heading: Employees get support in the flow of work"))
    a(para("Description: Atomicwork reads employee profiles, assets and "
           "department context, so answers arrive already personalised."))
    a(para("Note: media on the right"))
    a(para("<product screenshot>"))
    a(para())

    a(para("SECTION 5:"))
    a(para("Layout: quote"))
    a(para("Quote: Atomicwork cut our resolution time from days to minutes, "
           "and our team stopped firefighting."))
    a(para("Author: Jane Doe"))
    a(para("Role: Head of IT, Zuora"))
    a(para())

    a(para("SECTION 6:"))
    a(para("Layout: stat-band"))
    a(para("Heading: What teams see in the first quarter"))
    a(para("Stat: 65% of requests resolved without a human"))
    a(para("Stat: 4x faster first response"))
    a(para("Stat: 12 hours a week returned to each agent"))
    a(para())

    a(para("SECTION 7:"))
    a(para("Layout: cta-band"))
    a(para("Heading: Ready to provide delightful employee service?"))
    a(para("Description: Get started in days, not quarters."))
    a(para("Button: Get a demo"))
    return "".join(p)


def write_docx(path, body):
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body>'
        + body
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
          '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" '
          'w:left="1134"/></w:sectPr>'
        '</w:body></w:document>'
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    parts = [
        ("[Content_Types].xml", CONTENT_TYPES),
        ("_rels/.rels", ROOT_RELS),
        ("word/_rels/document.xml.rels", DOC_RELS),
        ("word/document.xml", document),
        ("word/styles.xml", STYLES),
        ("word/numbering.xml", NUMBERING),
    ]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts:
            # Fixed timestamps keep the output byte-identical between runs, so
            # regenerating an unchanged template produces no git diff.
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    print("Wrote %s (%d bytes)" % (path, os.path.getsize(path)))


def main():
    write_docx(TEMPLATE_OUT, build_body())
    write_docx(EXAMPLE_OUT, build_example())


if __name__ == "__main__":
    main()
