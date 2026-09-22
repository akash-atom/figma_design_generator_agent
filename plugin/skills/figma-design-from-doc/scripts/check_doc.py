#!/usr/bin/env python3
"""Check a .docx against the page spec format in references/doc-format.md.

Standard library only. Reuses docx_extract.py, so what it checks is exactly what
the design generator will see.

Usage:
    check_doc.py DOC.docx [--json] [--strict]

Exit codes: 0 clean (or warnings only), 1 errors found, 2 could not read the file.
Use --strict to fail on warnings too.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx_extract import (  # noqa: E402
    Docx, LAYOUTS, build_sections, detect_structure, parse_body)

PLACEHOLDER_COPY = ("tbd", "tba", "todo", "lorem ipsum", "xxx", "placeholder",
                    "coming soon", "fill this in", "?")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.notes = []

    def error(self, where, msg, fix):
        self.errors.append({"where": where, "message": msg, "fix": fix})

    def warn(self, where, msg, fix):
        self.warnings.append({"where": where, "message": msg, "fix": fix})

    def note(self, where, msg):
        self.notes.append({"where": where, "message": msg})


def section_label(sec):
    if sec.get("index"):
        return "SECTION %d" % sec["index"]
    if sec.get("kind") == "preamble":
        return "page header"
    return "H%d %s" % (sec.get("level", 1), sec.get("heading") or "(untitled)")


def first_role(sec, role):
    values = (sec.get("roles") or {}).get(role) or []
    return values[0] if values else None


def has_label(sec, role):
    """The label is present, even if its value is blank."""
    return bool((sec.get("roles") or {}).get(role))


def looks_placeholder(text):
    stripped = (text or "").strip().lower().rstrip(".")
    return stripped in PLACEHOLDER_COPY or stripped.startswith("tbd")


def check_page_header(model, rep):
    page, present = None, False
    for block in model["blocks"]:
        if block.get("role") == "page":
            page, present = block.get("value"), True
            break
        if block["type"] == "section_marker":
            break
    if present and not page:
        rep.error("page header", "'Page:' is present but has no value.",
                  "Write the page name after the colon, e.g. "
                  "'Page: Employee self-service'.")
    elif not page:
        rep.error("page header",
                  "No 'Page:' line found above SECTION 1.",
                  "Add 'Page: <short page name>' as the first line. It names "
                  "the Figma frame.")
    elif len(page) > 60:
        rep.warn("page header",
                 "'Page:' is %d characters -- it becomes the Figma frame name."
                 % len(page),
                 "Shorten it to the page's name, e.g. 'Employee self-service'.")
    return page


def check_section(sec, rep):
    where = section_label(sec)

    HEADLESS_OK = ("quote", "logo-band", "footer")
    heading = first_role(sec, "heading")
    if not heading and has_label(sec, "heading"):
        rep.error(where, "'Heading:' is present but has no value.",
                  "Write the headline after the colon, or delete the label.")
    elif not heading:
        if sec.get("placeholders") and not sec["roles"]:
            rep.warn(where,
                     "No 'Heading:' -- section contains only %s."
                     % ", ".join("<%s>" % p for p in sec["placeholders"]),
                     "Add 'Heading: ...', or confirm this section is "
                     "intentionally visual-only.")
        elif sec.get("layout") in HEADLESS_OK:
            pass  # a quote, logo band or footer needs no headline
        else:
            rep.error(where, "No 'Heading:' line.",
                      "Add 'Heading: <the section headline>'. Every section "
                      "needs one except quote, logo-band and footer.")
    elif looks_placeholder(heading):
        rep.error(where, "'Heading:' is placeholder copy (%r)." % heading,
                  "Write the real headline, or remove the label so the "
                  "section is reported as incomplete instead of shipping "
                  "'TBD' into the design.")

    declared = sec.get("layoutDeclared")
    if declared and not sec.get("layout"):
        rep.error(where, "'Layout: %s' is not a known archetype." % declared,
                  "Use one of: %s." % ", ".join(LAYOUTS))

    layout = sec.get("layout")
    roles = sec.get("roles") or {}

    if layout == "quote":
        if not roles.get("quote"):
            rep.error(where, "Layout is 'quote' but there is no 'Quote:' line.",
                      "Add 'Quote: <the testimonial>'.")
        if not roles.get("attribution"):
            rep.warn(where, "Quote has no 'Author:'.",
                     "Add 'Author: <name>' and optionally 'Role: <title, "
                     "company>'.")
    if layout == "stat-band" and not roles.get("stat"):
        rep.error(where, "Layout is 'stat-band' but there are no 'Stat:' lines.",
                  "Add one 'Stat:' line per number.")
    if layout in ("feature-grid", "accordion"):
        items = [b for b in sec["blocks"] if b["type"] == "list"]
        count = sum(len(b["items"]) for b in items)
        if count == 0:
            rep.error(where,
                      "Layout is '%s' but the section has no bulleted list."
                      % layout,
                      "Add one bullet per card/entry, in the form "
                      "'- Title -- body'.")
        elif layout == "feature-grid" and count > 8:
            rep.warn(where, "%d grid items is a lot for one section." % count,
                     "Split into two sections, or switch to "
                     "'Layout: accordion'.")
    if layout == "cta-band" and not roles.get("cta"):
        rep.warn(where, "Layout is 'cta-band' but there is no 'Button:' line.",
                 "Add 'Button: <label>'.")
    if layout == "hero" and not roles.get("cta"):
        rep.warn(where, "Hero has no 'Button:' line.",
                 "Add 'Button: <label>' unless the hero is deliberately "
                 "CTA-free.")

    if len(roles.get("cta") or []) > 2:
        rep.warn(where, "%d CTAs in one section." % len(roles["cta"]),
                 "Most components take a primary and a secondary. Use "
                 "'Button:' and 'Button 2:'.")

    # Unlabelled prose in a labelled section is ambiguous.
    bare = [b for b in sec["blocks"]
            if b["type"] == "paragraph" and not b.get("marker")
            and len(b["text"]) > 40]
    if bare:
        rep.warn(where,
                 "%d unlabelled paragraph(s) -- these will be guessed at."
                 % len(bare),
                 "Label them ('Description:', 'Note:'), or delete them if "
                 "they are working notes. First: %r"
                 % (bare[0]["text"][:70] + "..."))

    for block in sec["blocks"]:
        if block.get("externalUrl"):
            rep.error(where, "Linked (not pasted) image: %s"
                      % block["externalUrl"][:60],
                      "Paste the image into the document. Figma cannot fetch "
                      "image URLs.")


def check_structure(model, rep):
    structure = model["structure"]
    if structure == "headings":
        rep.note("document",
                 "Word heading styles detected, not 'SECTION n:' markers. "
                 "Read as a long-form document (H1 title, H2 per section). "
                 "That's correct for blog posts; page specs should use the "
                 "labelled format.")
        return False
    if structure == "flat":
        rep.error("document",
                  "No 'SECTION n:' markers and no Word heading styles found.",
                  "Add 'SECTION 1:', 'SECTION 2:' ... lines to mark where each "
                  "page section starts. See references/doc-format.md.")
        return False

    indices = [s["index"] for s in model["sections"] if s.get("index")]
    if indices and indices != sorted(indices):
        rep.warn("document",
                 "Section numbers are out of order: %s."
                 % ", ".join(str(i) for i in indices),
                 "Renumber them. Document order decides page order, so the "
                 "numbers should agree with it.")
    return True


def render(rep, model, page, labelled):
    out = []
    out.append("Document: %s" % os.path.basename(model["source"]))
    out.append("Structure: %s%s" % (
        model["structure"],
        "  (page spec)" if labelled else "  (long-form)"))
    if page:
        out.append("Page name: %s" % page)
    out.append("Sections: %d" % len(model["sections"]))
    out.append("")

    for kind, items, symbol in (("ERROR", rep.errors, "x"),
                                ("WARNING", rep.warnings, "!")):
        if not items:
            continue
        out.append("%s (%d)" % (kind + "S", len(items)))
        for item in items:
            out.append("  %s %s: %s" % (symbol, item["where"], item["message"]))
            out.append("      fix: %s" % item["fix"])
        out.append("")

    if rep.notes:
        out.append("NOTES")
        for item in rep.notes:
            out.append("  - %s: %s" % (item["where"], item["message"]))
        out.append("")

    if not rep.errors and not rep.warnings:
        out.append("Clean -- this document is ready to generate from.")
    elif not rep.errors:
        out.append("No errors. The warnings above are places the design will "
                   "be guessed at rather than specified.")
    else:
        out.append("Fix the errors above before generating. See "
                   "references/doc-format.md for the format.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="path to the .docx file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print("Error: no such file: %s" % args.input, file=sys.stderr)
        return 2

    dx = Docx(args.input)
    # A format check needs the block structure, not the images -- extract to a
    # temp dir so nothing lands next to the user's document.
    tmp = tempfile.mkdtemp(prefix="doccheck-")
    try:
        blocks, _ = parse_body(dx, os.path.join(tmp, "assets"), "assets")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    structure = detect_structure(blocks)
    model = {
        "source": os.path.abspath(args.input),
        "structure": structure,
        "blocks": blocks,
        "sections": build_sections(blocks, structure),
    }

    rep = Report()
    labelled = check_structure(model, rep)
    page = check_page_header(model, rep) if labelled else None
    if labelled:
        real = [s for s in model["sections"]
                if s.get("kind") != "preamble"]
        for sec in real:
            check_section(sec, rep)
        missing = [section_label(s) for s in real
                   if not s.get("layoutDeclared")]
        if missing:
            rep.warn("document",
                     "No 'Layout:' line in %d of %d sections (%s) -- their "
                     "archetypes will be inferred from content shape."
                     % (len(missing), len(real), ", ".join(missing)),
                     "Add 'Layout: <archetype>' to each. Options: %s."
                     % ", ".join(LAYOUTS))

    if args.json:
        print(json.dumps({
            "document": model["source"],
            "structure": structure,
            "pageName": page,
            "sectionCount": len(model["sections"]),
            "errors": rep.errors,
            "warnings": rep.warnings,
            "notes": rep.notes,
        }, indent=2))
    else:
        print(render(rep, model, page, labelled))

    if rep.errors:
        return 1
    return 1 if (args.strict and rep.warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
