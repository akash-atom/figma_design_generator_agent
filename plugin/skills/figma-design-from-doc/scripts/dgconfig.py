#!/usr/bin/env python3
"""Resolve and persist figma-design-generator configuration.

Standard library only. Three layers, highest priority first:

  1. ./.figma-design/config.json                        (project)
  2. ~/.claude/figma-design-generator/config.json       (user)
  3. <plugin>/config/defaults.json                      (team defaults)

Usage:
    dgconfig.py show                       # resolved config + where each value came from
    dgconfig.py paths                      # the three layer paths and whether they exist
    dgconfig.py set --library-key K --library-name N [--scope project|user]
    dgconfig.py cache-status               # is the library map cached and still valid?
"""

import argparse
import json
import os
import sys

PROJECT_DIR = ".figma-design"
USER_DIR = os.path.expanduser("~/.claude/figma-design-generator")


def plugin_defaults_path():
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        p = os.path.join(root, "config", "defaults.json")
        if os.path.exists(p):
            return p
    # scripts/ -> figma-design-from-doc/ -> skills/ -> plugin/
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(
        os.path.join(here, "..", "..", "..", "config", "defaults.json"))


def layer_paths():
    return [
        ("project", os.path.join(os.getcwd(), PROJECT_DIR, "config.json")),
        ("user", os.path.join(USER_DIR, "config.json")),
        ("plugin", plugin_defaults_path()),
    ]


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (IOError, OSError):
        return {}
    except ValueError as exc:
        raise SystemExit("Error: %s is not valid JSON (%s)" % (path, exc))


def resolve():
    """Merge the layers two levels deep, tracking which layer won."""
    merged, provenance = {}, {}
    for scope, path in reversed(layer_paths()):  # lowest priority first
        data = load(path)
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                for sub, subval in value.items():
                    if subval is None:
                        continue
                    merged[key][sub] = subval
                    provenance["%s.%s" % (key, sub)] = scope
            else:
                if value is None and key in merged:
                    continue
                merged[key] = json.loads(json.dumps(value))
                provenance[key] = scope
                if isinstance(value, dict):
                    for sub, subval in value.items():
                        if subval is not None:
                            provenance["%s.%s" % (key, sub)] = scope
    return merged, provenance


def library_map_path():
    return os.path.join(os.getcwd(), PROJECT_DIR, "library-map.json")


def cmd_show(args):
    cfg, prov = resolve()
    lib = cfg.get("library", {})
    print(json.dumps(cfg, indent=2))
    print("\n# provenance")
    for key in sorted(prov):
        print("%-28s %s" % (key, prov[key]))
    mode = lib.get("mode") or ("local" if lib.get("libraryFileKey")
                               and lib.get("libraryFileKey")
                               == cfg.get("targetFileKey") else "published")
    print("\n# resolved mode: %s" % mode)
    if mode == "local":
        print("  Components are referenced by node id inside one file. "
              "No publishing required.")
    else:
        print("  Components are imported across files by key. The library "
              "must be published.")
    if not lib.get("libraryKey") and not lib.get("libraryFileKey"):
        print("\n! No component library pinned. Run /figma-library-setup.")
    return 0


def cmd_paths(args):
    for scope, path in layer_paths():
        print("%-8s %-70s %s" % (
            scope, path, "exists" if os.path.exists(path) else "-"))
    lm = library_map_path()
    print("%-8s %-70s %s" % (
        "libmap", lm, "exists" if os.path.exists(lm) else "-"))
    return 0


def cmd_set(args):
    target_dir = os.path.join(os.getcwd(), PROJECT_DIR) \
        if args.scope == "project" else USER_DIR
    path = os.path.join(target_dir, "config.json")
    data = load(path)
    lib = data.setdefault("library", {})
    for attr, key in (("library_key", "libraryKey"),
                      ("library_name", "libraryName"),
                      ("library_file_key", "libraryFileKey"),
                      ("mode", "mode")):
        value = getattr(args, attr)
        if value is not None:
            lib[key] = value
    if args.file_key is not None:
        data["targetFileKey"] = args.file_key
    if args.doc is not None:
        data["lastDocument"] = os.path.abspath(args.doc)
    os.makedirs(target_dir, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print("Wrote %s" % path)
    print(json.dumps(data, indent=2))
    return 0


def cmd_cache_status(args):
    cfg, _ = resolve()
    want = (cfg.get("library") or {}).get("libraryKey")
    path = library_map_path()
    if not os.path.exists(path):
        print("MISS: no %s -- run library discovery." % path)
        return 1
    data = load(path)
    have = data.get("libraryKey") or data.get("libraryFileKey")
    want = want or (cfg.get("library") or {}).get("libraryFileKey")
    if want and have and want != have:
        print("STALE: cached map is for library %s but config pins %s -- "
              "rediscover." % (have, want))
        return 1
    n = len(data.get("components") or {})
    print("HIT: %s (%d components, %d variables, %d styles) for library %s"
          % (path, n, len(data.get("variables") or {}),
             len(data.get("styles") or {}), have or "?"))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("show")
    sub.add_parser("paths")
    sub.add_parser("cache-status")
    st = sub.add_parser("set")
    st.add_argument("--library-key")
    st.add_argument("--library-name")
    st.add_argument("--library-file-key")
    st.add_argument("--mode", choices=["local", "published"],
                    help="local: components live in the same file we build "
                         "into, referenced by node id (works with an "
                         "unpublished library). published: imported across "
                         "files by key.")
    st.add_argument("--file-key", help="target Figma file key to build into")
    st.add_argument("--doc", help="path of the source .docx, for reference")
    st.add_argument("--scope", choices=["project", "user"], default="project")
    args = ap.parse_args()
    handlers = {"show": cmd_show, "paths": cmd_paths,
                "set": cmd_set, "cache-status": cmd_cache_status}
    if args.cmd not in handlers:
        ap.print_help()
        return 2
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
