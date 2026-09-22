#!/usr/bin/env python3
"""Read a content model and propose a page design for it.

Standard library only. Takes the output of docx_extract.py and works out, from
the shape of the writing alone, where the sections are and what layout each one
wants. The writer does not have to mark anything up.

This produces a *proposal with reasons*, not a verdict. The agent reviews it
against what the component library actually offers and can override any row --
the `reasons` on each candidate are there to be argued with.

Usage:
    analyze_content.py .figma-design/content.json [--out analysis.json] [--quiet]
"""

import argparse
import json
import os
import re
import sys

ARCHETYPES = ("hero", "logo-band", "feature-grid", "feature-split",
              "stat-band", "quote", "accordion", "table", "cta-band",
              "prose", "footer")

CTA_VERBS = ("get", "book", "start", "try", "see", "talk", "request",
             "download", "join", "sign", "schedule", "explore", "learn",
             "contact", "discover", "watch", "read", "find out", "switch",
             "meet", "ready")

# Numbers that read as a metric rather than as prose.
METRIC_RE = re.compile(
    r"(\d+(\.\d+)?\s*(%|x|×|k\b|m\b|bn\b|\+))"
    r"|(\b\d+(\.\d+)?\s*(hours?|days?|weeks?|months?|quarters?|minutes?|"
    r"seconds?|times|per cent|percent)\b)", re.I)

SOCIAL_PROOF_RE = re.compile(
    r"\b(trusted by|used by|join(ed)? \d|customers|companies|teams "
    r"(use|trust)|powering|loved by|\d+[,\d]* (teams|companies|customers))\b",
    re.I)

# "Device Ops Engineer. Handles hardware-related support tickets..." --
# a card written as a paragraph. Writers do this constantly; a designer reads
# a run of them as a grid, so the analyser has to as well.
IMPLICIT_ITEM_RE = re.compile(
    r"^(?P<lead>[A-Z][^.!?\u2013\u2014]{2,48})"
    r"(?:\.|\s*[\u2013\u2014]|:)\s+(?P<body>\S.{10,})$")

ATTRIBUTION_RE = re.compile(
    r"^[A-Z][A-Za-z.'-]+(?: [A-Z][A-Za-z.'-]+){1,3}\s*[,–—-]\s*\S")

QUOTE_RE = re.compile(r"[“”\"]")


# --------------------------------------------------------------------------
# section boundary inference, for documents with no structure at all
# --------------------------------------------------------------------------

def looks_like_heading(block, nxt):
    """A writer who types without heading styles still writes headings."""
    if block["type"] != "paragraph" or block.get("marker"):
        return False
    text = block["text"]
    words = len(text.split())
    if words == 0 or words > 16:
        return False
    if block.get("allBold"):
        return True
    if text.endswith(":"):
        return True
    # No terminal punctuation and something substantial follows it.
    if not text.rstrip().endswith((".", "!", "?", ";", ",")):
        if nxt is not None and (
                nxt["type"] == "list"
                or (nxt["type"] == "paragraph"
                    and len(nxt["text"].split()) > words)):
            return True
    return False


def infer_boundaries(blocks):
    """Group an unstructured block list into candidate sections."""
    sections, current = [], None
    for i, block in enumerate(blocks):
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if looks_like_heading(block, nxt):
            current = {"heading": block["text"], "level": 2, "index": None,
                       "kind": "inferred", "blocks": [], "subsections": [],
                       "roles": {}, "placeholders": [],
                       "layout": None, "layoutDeclared": None}
            sections.append(current)
            continue
        if current is None:
            current = {"heading": None, "level": 2, "index": None,
                       "kind": "inferred", "blocks": [], "subsections": [],
                       "roles": {}, "placeholders": [],
                       "layout": None, "layoutDeclared": None}
            sections.append(current)
        current["blocks"].append(block)
    return sections


def flatten(sections, out=None):
    """Depth-first flatten, so an H2 under an H1 becomes its own page section.

    A parent heading that carries copy of its own stays as a section; one that
    only introduces its children does not become an empty band.
    """
    out = out if out is not None else []
    for sec in sections:
        has_own = any(b["type"] in ("paragraph", "list", "table", "image",
                                    "placeholder")
                      for b in sec["blocks"])
        if has_own or not sec["subsections"]:
            out.append(sec)
        elif sec["subsections"]:
            # Keep the heading as a lead-in on the first child.
            sec["subsections"][0].setdefault("leadInHeading", sec["heading"])
        flatten(sec["subsections"], out)
    return out


# --------------------------------------------------------------------------
# signals
# --------------------------------------------------------------------------

def implicit_item_runs(paras):
    """Longest run of consecutive paragraphs that read as 'Lead-in. Body.'

    Returns (run_length, [lead-ins]) for the longest run found.
    """
    best, best_leads = 0, []
    run, leads = 0, []
    for para in paras:
        m = IMPLICIT_ITEM_RE.match(para["text"].strip())
        if m:
            run += 1
            leads.append(m.group("lead").strip())
            if run > best:
                best, best_leads = run, list(leads)
        else:
            run, leads = 0, []
    return best, best_leads


# Labels that carry no page copy -- excluded from shape measurements.
NON_COPY_ROLES = ("meta", "note", "layout", "page")


def copy_text(block):
    """The words a reader will actually see in this block."""
    if block.get("role") and "value" in block:
        return block["value"]
    return block.get("text", "")


def signals(sec, position, total):
    blocks = sec["blocks"]
    # A labelled paragraph is still copy -- 'Description: ...' is body text.
    # Only metadata and author notes are excluded, or every shape measurement
    # reads zero on a well-labelled document.
    paras = [b for b in blocks
             if b["type"] == "paragraph"
             and b.get("role") not in NON_COPY_ROLES]
    unlabelled = [b for b in paras if not b.get("marker")]
    lists = [b for b in blocks if b["type"] == "list"]
    items = [i for b in lists for i in b["items"]]
    images = [b for b in blocks if b["type"] == "image"]
    tables = [b for b in blocks if b["type"] == "table"]
    roles = sec.get("roles") or {}

    body = " ".join(copy_text(p) for p in paras)
    words = len(body.split())
    item_words = [len(i["text"].split()) for i in items]
    with_bodies = sum(1 for i in items
                      if re.search(r"\s[–—-]\s|: ", i["text"]))
    metric_items = sum(1 for i in items if METRIC_RE.search(i["text"]))
    question_items = sum(1 for i in items if i["text"].rstrip().endswith("?"))

    parallel = False
    if len(item_words) >= 2:
        spread = max(item_words) - min(item_words)
        parallel = spread <= max(6, 0.6 * (sum(item_words) / len(item_words)))

    implicit_n, implicit_leads = implicit_item_runs(unlabelled)
    implicit_words = [len(p["text"].split()) for p in unlabelled
                      if IMPLICIT_ITEM_RE.match(p["text"].strip())]
    implicit_metric = sum(
        1 for p in unlabelled
        if IMPLICIT_ITEM_RE.match(p["text"].strip())
        and METRIC_RE.search(p["text"]))

    last_para = copy_text(paras[-1]) if paras else ""
    heading = sec.get("heading") or ""
    first_word = (last_para.split() or [""])[0].lower().strip(",.")

    return {
        "position": position,
        "isFirst": position == 0,
        "isLast": position == total - 1,
        "headingWords": len(heading.split()),
        "paragraphCount": len(paras),
        "wordCount": words,
        "longestParagraphWords": max(
            (len(copy_text(p).split()) for p in paras), default=0),
        "unlabelledParagraphCount": len(unlabelled),
        "listItemCount": len(items),
        "listItemWordsAvg": round(sum(item_words) / len(item_words), 1)
        if item_words else 0,
        "listItemsParallel": parallel,
        "listItemsWithBodies": with_bodies,
        "implicitItemCount": implicit_n,
        "implicitItemLeads": implicit_leads[:8],
        "implicitItemWordsAvg": round(
            sum(implicit_words) / len(implicit_words), 1)
        if implicit_words else 0,
        "implicitMetricItems": implicit_metric,
        "metricItems": metric_items,
        "questionItems": question_items,
        "imageCount": len(images),
        "tableRowCount": sum(len(t["allRows"]) for t in tables),
        "placeholders": sec.get("placeholders") or [],
        "declaredLayout": sec.get("layout"),
        "hasQuoteMarks": bool(QUOTE_RE.search(body)),
        "hasAttribution": any(ATTRIBUTION_RE.match(copy_text(p))
                              for p in paras)
        or bool((sec.get("roles") or {}).get("attribution")),
        "hasSocialProof": bool(SOCIAL_PROOF_RE.search(body + " " + heading)),
        "metricInBody": bool(METRIC_RE.search(body)),
        "closingImperative": first_word in CTA_VERBS and len(
            last_para.split()) <= 14,
        "headingIsQuestion": heading.rstrip().endswith("?"),
        "explicitCtas": len(roles.get("cta") or []),
        "roles": sorted(roles),
    }


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

def score(sig):
    """Return {archetype: (score, [reasons])}. Scores are comparable, not
    probabilities."""
    s = {a: [0, []] for a in ARCHETYPES}

    def add(arch, points, reason):
        s[arch][0] += points
        s[arch][1].append("%+d %s" % (points, reason))

    # --- the author said so ------------------------------------------------
    if sig["declaredLayout"]:
        add(sig["declaredLayout"], 200,
            "author wrote 'Layout: %s'" % sig["declaredLayout"])

    # --- hero --------------------------------------------------------------
    if sig["isFirst"]:
        add("hero", 55, "opens the page")
        if sig["headingWords"] and sig["headingWords"] <= 14:
            add("hero", 15, "short headline (%d words)" % sig["headingWords"])
        if 10 <= sig["wordCount"] <= 140:
            add("hero", 12, "intro-length copy (%d words)" % sig["wordCount"])
        if sig["explicitCtas"] or sig["closingImperative"]:
            add("hero", 10, "has a call to action")
    else:
        add("hero", -60, "not the first section")

    # --- logo band ---------------------------------------------------------
    # Gated on shape: social-proof wording inside a long section is prose
    # about customers, not a logo strip.
    logo_shaped = (sig["wordCount"] < 60
                   and not sig["listItemCount"]
                   and sig["implicitItemCount"] < 3)
    if sig["hasSocialProof"] and logo_shaped:
        add("logo-band", 50, "social-proof wording in a short, list-free "
                             "section")
        if 1 <= sig["position"] <= 2:
            add("logo-band", 12, "sits just after the hero")
    elif sig["hasSocialProof"]:
        add("logo-band", 8, "mentions customers, but the section is too long "
                            "to be a logo strip")

    # --- feature grid ------------------------------------------------------
    n = sig["listItemCount"]
    if 3 <= n <= 6:
        add("feature-grid", 45, "%d list items -- grid-sized" % n)
    elif n in (2, 7, 8):
        add("feature-grid", 25, "%d list items" % n)
    elif n > 8:
        add("feature-grid", -15, "%d items is too many for a grid" % n)
    if n and sig["listItemsParallel"]:
        add("feature-grid", 15, "items are similar lengths")
    if sig["listItemsWithBodies"] >= max(2, n * 0.6):
        add("feature-grid", 12, "items have title/body structure")

    # Cards written as parallel paragraphs rather than as a bullet list.
    m = sig["implicitItemCount"]
    if m >= 3 and n == 0:
        if m <= 6:
            add("feature-grid", 50,
                "%d consecutive '%s'-style paragraphs read as cards"
                % (m, (sig["implicitItemLeads"] or [""])[0][:24]))
        else:
            add("feature-grid", 30,
                "%d parallel paragraphs -- grid, but crowded" % m)
        if sig["implicitItemWordsAvg"] <= 34:
            add("feature-grid", 12,
                "each averages %s words -- card-sized"
                % sig["implicitItemWordsAvg"])
        elif sig["implicitItemWordsAvg"] > 40:
            add("feature-grid", -30,
                "each averages %s words -- too much copy for a card"
                % sig["implicitItemWordsAvg"])
        add("prose", -25,
            "%d parallel paragraphs are structured content, not flowing prose"
            % m)

    # --- accordion ---------------------------------------------------------
    if n >= 6:
        add("accordion", 40, "%d items -- long list" % n)
    if sig["questionItems"] >= 2:
        add("accordion", 35, "%d items are questions" % sig["questionItems"])
    if sig["headingIsQuestion"]:
        add("accordion", 10, "heading is a question")
    if m >= 6 and n == 0:
        add("accordion", 30, "%d parallel paragraphs -- long enough to "
                             "collapse" % m)
    if m >= 3 and sig["implicitItemWordsAvg"] > 40:
        add("accordion", 20,
            "parallel paragraphs average %s words -- too long for cards"
            % sig["implicitItemWordsAvg"])
    if n and sig["listItemWordsAvg"] > 40:
        add("feature-grid", -25,
            "items average %s words -- too much copy for a card"
            % sig["listItemWordsAvg"])
    if n and sig["listItemWordsAvg"] > 28:
        add("accordion", 20,
            "items average %s words -- too long for cards"
            % sig["listItemWordsAvg"])

    # --- stat band ---------------------------------------------------------
    if n and sig["metricItems"] >= 2:
        ratio = sig["metricItems"] / n
        if ratio >= 0.6:
            add("stat-band", 55,
                "%d of %d items are metrics" % (sig["metricItems"], n))
        else:
            add("stat-band", 20,
                "%d items contain metrics" % sig["metricItems"])
        if sig["listItemWordsAvg"] <= 12:
            add("stat-band", 15, "items are short")

    if m >= 2 and sig["implicitMetricItems"] >= 2:
        add("stat-band", 40,
            "%d parallel paragraphs lead with a metric"
            % sig["implicitMetricItems"])

    # --- quote -------------------------------------------------------------
    if sig["hasQuoteMarks"]:
        add("quote", 45, "copy is in quotation marks")
    if sig["hasAttribution"]:
        add("quote", 35, "a name-and-title line is present")
    if sig["hasQuoteMarks"] and sig["wordCount"] < 80:
        add("quote", 15, "short enough to be a pull quote")

    # --- table -------------------------------------------------------------
    if sig["tableRowCount"] >= 2:
        add("table", 85, "%d-row table in the source" % sig["tableRowCount"])

    # --- feature split -----------------------------------------------------
    if sig["imageCount"] == 1 and n == 0:
        add("feature-split", 40, "one image, no list")
    if sig["imageCount"] == 1 and 30 <= sig["wordCount"] <= 220:
        add("feature-split", 15, "copy pairs with a single visual")
    if not sig["imageCount"] and n == 0 and 40 <= sig["wordCount"] <= 180:
        add("feature-split", 20,
            "prose block that reads better beside a visual")

    # --- cta band ----------------------------------------------------------
    if sig["isLast"]:
        add("cta-band", 40, "closes the page")
    if sig["closingImperative"]:
        add("cta-band", 30, "ends on an imperative")
    if sig["explicitCtas"]:
        add("cta-band", 15, "has an explicit button")
    if sig["wordCount"] > 120:
        add("cta-band", -25, "too much copy for a CTA band")

    # --- prose -------------------------------------------------------------
    if sig["wordCount"] > 180 and n == 0 and sig["implicitItemCount"] < 3:
        add("prose", 45,
            "%d words of unbroken copy -- will not fit a card"
            % sig["wordCount"])
    if sig["unlabelledParagraphCount"] >= 4:
        add("prose", 20,
            "%d unlabelled paragraphs" % sig["unlabelledParagraphCount"])
    if sig["longestParagraphWords"] > 90:
        add("prose", 20,
            "longest paragraph is %d words" % sig["longestParagraphWords"])

    # --- explicit component request ---------------------------------------
    for ph in sig["placeholders"]:
        arch = placeholder_archetype(ph)
        if arch:
            add(arch, 60, "author asked for <%s>" % ph)

    return {a: (v[0], v[1]) for a, v in s.items()}


def rank(scored, limit=3):
    ordered = sorted(scored.items(), key=lambda kv: -kv[1][0])
    return [{"archetype": a, "score": v[0], "reasons": v[1]}
            for a, v in ordered[:limit] if v[0] > 0]


# --------------------------------------------------------------------------
# page-level narrative
# --------------------------------------------------------------------------

def document_kind(rows):
    """Marketing page or long-form article? They want different layouts, and
    forcing an article into page bands is the classic failure."""
    if not rows:
        return "unknown", "no sections found"
    prose = sum(1 for r in rows if r["proposed"] == "prose")
    ctas = sum(1 for r in rows
               if r["proposed"] == "cta-band"
               or r["signals"]["explicitCtas"]
               or r["signals"]["closingImperative"])
    structured = sum(1 for r in rows
                     if r["signals"]["listItemCount"] >= 3
                     or r["signals"]["implicitItemCount"] >= 3
                     or r["signals"]["metricItems"] >= 2)
    words = sum(r["signals"]["wordCount"] for r in rows)
    avg = words / len(rows)

    if prose / len(rows) >= 0.5 and ctas == 0 and avg > 180:
        return "article", (
            "%d of %d sections are unbroken prose averaging %d words, with no "
            "call to action. This reads as a blog post or long-form article, "
            "not a marketing page." % (prose, len(rows), avg))
    if structured >= 2 and ctas >= 1:
        return "marketing-page", (
            "%d sections carry structured content and the page asks the "
            "reader to act." % structured)
    if avg < 90 and len(rows) >= 4:
        return "marketing-page", "short, banded sections throughout"
    return "mixed", (
        "part structured page, part long-form copy -- confirm which the "
        "reader is getting")


def page_notes(rows, kind):
    if kind == "article":
        return [{
            "issue": "This document is long-form, not a marketing page.",
            "detail": "Laying it out as hero + bands will stretch a few "
                      "hundred words of prose across a page of empty "
                      "sections.",
            "suggest": "Build it as an article: a title block, then a single "
                       "measure-constrained column of prose with the "
                       "library's text styles, pulling out a quote or stat "
                       "where the copy offers one. Confirm with the user "
                       "before treating it as a page."}] + _rhythm_notes(rows)
    return _page_notes(rows)


def _rhythm_notes(rows):
    """Checks that only make sense across the whole page."""
    notes = []
    heavy = [i + 1 for i, r in enumerate(rows)
             if r["signals"]["wordCount"] > 250]
    if heavy:
        notes.append({
            "issue": "Section(s) %s carry a lot of copy."
                     % ", ".join(str(i) for i in heavy),
            "detail": "Over 250 words will not fit any card or band "
                      "component.",
            "suggest": "Lay them out as prose blocks, or split them into "
                       "several sections. Do NOT shorten the writer's copy "
                       "to fit a component without asking."})
    return notes


def _page_notes(rows):
    notes = _rhythm_notes(rows)
    chosen = [r["proposed"] for r in rows]

    if chosen and chosen[0] != "hero":
        notes.append({
            "issue": "The page does not open with a hero.",
            "detail": "Section 1 reads as '%s'. A page normally needs one "
                      "opening statement." % chosen[0],
            "suggest": "Promote section 1 to a hero, or confirm this page "
                       "is a continuation of another."})

    if "cta-band" not in chosen:
        notes.append({
            "issue": "The page never asks the reader to do anything.",
            "detail": "No section reads as a call to action.",
            "suggest": "Add a closing CTA band. If the source has no closing "
                       "copy, say so rather than inventing a button label."})

    for i in range(1, len(chosen)):
        if chosen[i] == chosen[i - 1] and chosen[i] not in ("prose",):
            alts = [c["archetype"] for c in rows[i]["candidates"][1:2]]
            notes.append({
                "issue": "Sections %d and %d are both '%s'."
                         % (i, i + 1, chosen[i]),
                "detail": "Consecutive identical bands flatten the page's "
                          "rhythm.",
                "suggest": "Vary one of them%s, or alternate the background "
                           "and media side." % (
                               " (next best for section %d: %s)"
                               % (i + 1, alts[0]) if alts else "")})

    visuals = sum(1 for r in rows
                  if r["proposed"] in ("feature-split", "logo-band",
                                       "stat-band", "quote"))
    if len(rows) >= 5 and visuals == 0:
        notes.append({
            "issue": "No visual relief across %d sections." % len(rows),
            "detail": "Every section is text in the same shape.",
            "suggest": "Break the run with a stat band, a quote, or a split "
                       "section with a visual."})

    return notes


PLACEHOLDER_ARCHETYPES = (
    ("logo-band", ("logo",)),
    ("feature-grid", ("grid", "cards", "tiles")),
    ("quote", ("testimonial", "quote")),
    ("accordion", ("accordion", "faq")),
    ("stat-band", ("stats", "metrics", "numbers")),
    ("feature-split", ("screenshot", "image", "video", "gif", "media",
                       "product")),
    ("table", ("table", "comparison")),
)


def placeholder_archetype(text):
    low = text.lower()
    for arch, words in PLACEHOLDER_ARCHETYPES:
        if any(word in low for word in words):
            return arch
    return None


def merge_orphans(sections):
    """A heading-less scrap of copy is part of the next section, not its own
    band. Writers leave these behind constantly -- a stray eyebrow line, a
    one-line lead-in above a heading."""
    out = []
    for sec in sections:
        content = [b for b in sec["blocks"]
                   if b["type"] in ("paragraph", "list", "table", "image",
                                    "placeholder")]
        words = sum(len(b.get("text", "").split()) for b in content)
        orphan = (not sec.get("heading") and words <= 12
                  and not any(b["type"] in ("image", "table", "list")
                              for b in content))
        if orphan and out is not None and sections.index(sec) < len(sections) - 1:
            nxt_index = sections.index(sec) + 1
            sections[nxt_index]["blocks"] = (
                sec["blocks"] + sections[nxt_index]["blocks"])
            for role, values in (sec.get("roles") or {}).items():
                sections[nxt_index].setdefault("roles", {}).setdefault(
                    role, []).extend(values)
            sections[nxt_index]["placeholders"] = (
                (sec.get("placeholders") or [])
                + (sections[nxt_index].get("placeholders") or []))
            continue
        out.append(sec)
    return out


def split_suggestion(sec, sig, proposed):
    """Does this section hold two page sections' worth of content?

    The common case: hero copy and a <logo grid> in the same authored section.
    A designer splits it without being asked; so should we.
    """
    for ph in sig["placeholders"]:
        arch = placeholder_archetype(ph)
        if not arch or arch == proposed:
            continue
        if sig["wordCount"] >= 25 or sig["listItemCount"] >= 3:
            return {
                "reason": "Section holds both %d words of copy and a "
                          "<%s> visual." % (sig["wordCount"], ph),
                "suggest": "Split into two page sections: a '%s' for the "
                           "copy, then a '%s' for the <%s>."
                           % (proposed, arch, ph),
                "into": [proposed, arch],
            }
    if sig["wordCount"] > 250 and sig["listItemCount"] >= 3:
        return {
            "reason": "Section has %d words of copy plus a %d-item list."
                      % (sig["wordCount"], sig["listItemCount"]),
            "suggest": "Split the copy into its own section above the grid.",
            "into": ["prose", proposed],
        }
    return None


def is_metadata_only(sec):
    """The page header block (Page:, SEO title:, slug) is not a page section."""
    content = [b for b in sec["blocks"]
               if b["type"] in ("paragraph", "list", "table", "image",
                                "placeholder")]
    if not content:
        return True
    return all(b.get("role") in ("meta", "page") for b in content)


def analyse(model, keep_blocks=False):
    """Propose a page design for a content model.

    keep_blocks attaches each section's source blocks to its row under
    `_blocks`, for callers that need to inspect the content itself. Strip it
    before serialising.
    """
    structure = model.get("structure")
    if structure == "flat":
        sections = infer_boundaries(model["blocks"])
        basis = "inferred from paragraph shape (document had no structure)"
    else:
        sections = flatten(model["sections"])
        basis = ("author's SECTION markers" if structure == "section-markers"
                 else "Word heading styles")

    sections = [s for s in sections if s["blocks"]
                and not is_metadata_only(s)]
    sections = merge_orphans(sections)
    rows, total = [], len(sections)
    for i, sec in enumerate(sections):
        sig = signals(sec, i, total)
        scored = score(sig)
        candidates = rank(scored)
        proposed = candidates[0]["archetype"] if candidates else "prose"
        confidence = "low"
        if candidates:
            top = candidates[0]["score"]
            runner = candidates[1]["score"] if len(candidates) > 1 else 0
            if top >= 60 and top - runner >= 25:
                confidence = "high"
            elif top >= 40:
                confidence = "medium"
        rows.append({
            "n": i + 1,
            "heading": sec.get("heading") or sec.get("leadInHeading"),
            "sectionKind": sec.get("kind"),
            "proposed": proposed,
            "confidence": confidence,
            "candidates": candidates,
            "split": split_suggestion(sec, sig, proposed),
            "signals": sig,
        })
        if keep_blocks:
            rows[-1]["_blocks"] = sec["blocks"]

    kind, kind_reason = document_kind(rows)
    return {"source": model.get("source"), "title": model.get("title"),
            "structure": structure, "sectioningBasis": basis,
            "documentKind": kind, "documentKindReason": kind_reason,
            "sectionCount": total, "sections": rows,
            "pageNotes": page_notes(rows, kind)}


def render(a):
    out = ["Title: %s" % a["title"],
           "Reads as: %s -- %s" % (a["documentKind"],
                                   a["documentKindReason"]),
           "Sectioning: %s" % a["sectioningBasis"],
           "Sections: %d" % a["sectionCount"], ""]
    out.append("Proposed layout")
    for row in a["sections"]:
        head = (row["heading"] or "(untitled)")
        out.append("  %2d. %-14s %-7s %s" % (
            row["n"], row["proposed"], "(%s)" % row["confidence"],
            head[:58]))
        for c in row["candidates"][:2]:
            out.append("        %-14s %3d  %s" % (
                c["archetype"], c["score"], "; ".join(c["reasons"][:3])))
        if row.get("split"):
            out.append("        SPLIT?        %s %s" % (
                row["split"]["reason"], row["split"]["suggest"]))
    if a["pageNotes"]:
        out.append("")
        out.append("Page-level notes")
        for note in a["pageNotes"]:
            out.append("  ! %s" % note["issue"])
            out.append("    %s" % note["detail"])
            out.append("    -> %s" % note["suggest"])
    low = [r["n"] for r in a["sections"] if r["confidence"] == "low"]
    if low:
        out.append("")
        out.append("Low confidence on section(s) %s -- decide these against "
                   "the library, not the score."
                   % ", ".join(str(i) for i in low))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="path to content.json from docx_extract.py")
    ap.add_argument("--out", default=None,
                    help="write the analysis JSON here "
                         "(default: alongside the input)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit("Error: no such file: %s" % args.input)
    with open(args.input) as fh:
        model = json.load(fh)

    result = analyse(model)
    for row in result["sections"]:
        row.pop("_blocks", None)
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.input)),
                                   "analysis.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    if not args.quiet:
        print(render(result))
        print("\nWrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
