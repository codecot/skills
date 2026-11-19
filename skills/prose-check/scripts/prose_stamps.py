#!/usr/bin/env python3
"""Scan English prose for LLM writing stamps. Reads, changes nothing.

    python3 prose_stamps.py [--skip REGEX] FILE [FILE...]

--skip drops lines matching REGEX (service labels, notes) before scanning.

Two kinds of checks:
  * phrases   - regex catalogue in prose_stamps.json (fake contrasts, drama,
                empty analysis, vague claims, fake authority, chat filler,
                LLM vocabulary).
  * structure - em-dash density, staccato runs (3+ short sentences in a row),
                parallel openers (neighbouring sentences starting with the same
                word), short aphoristic closer.

A file is split into blocks on lines that are exactly '---'; headings ('#')
are skipped. Severity: HIT = a stamp, hint = look at it yourself.
Exit code 1 when any HIT is found, so it can gate a rail.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SENT = re.compile(r"(?:[^.!?…]|(?<=\d)\.(?=\d))+[.!?…]+[\"')\]]*|(?:[^.!?…]|(?<=\d)\.(?=\d))+$")
WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")
SHORT = 6          # words; a sentence this short counts as staccato
DASH_RATE = 1.0    # em dashes per 100 words above which we flag


def load_catalogue():
    with open(os.path.join(HERE, "prose_stamps.json"), encoding="utf-8") as fh:
        raw = json.load(fh)
    cat = []
    for name, body in raw.items():
        if name.startswith("_"):
            continue
        for pat in body["patterns"]:
            cat.append((name, body["severity"], re.compile(pat, re.I)))
    return cat


def blocks(lines, skip=None):
    cur = []
    for no, line in enumerate(lines, 1):
        if skip and skip.search(line):
            continue
        if line.strip() == "---":
            if cur:
                yield cur
            cur = []
        elif line.strip() and not line.lstrip().startswith("#"):
            cur.append((no, line.rstrip("\n")))
    if cur:
        yield cur


def sentences(block):
    out = []
    for no, line in block:
        for m in SENT.finditer(line):
            s = m.group().strip()
            if WORD.search(s):
                out.append((no, s, len(WORD.findall(s))))
    return out


def scan_block(block, cat):
    found = []
    text_words = 0
    dashes = 0
    for no, line in block:
        text_words += len(WORD.findall(line))
        dashes += line.count("—")
        for name, sev, rx in cat:
            for m in rx.finditer(line):
                found.append((no, sev, name, m.group().strip()))
    sents = sentences(block)
    # phrases that span a sentence boundary on one line are caught above;
    # structure checks work on the sentence list.
    i = 0
    while i < len(sents):
        j = i
        while j < len(sents) and sents[j][2] <= SHORT:
            j += 1
        if j - i >= 3:
            found.append((sents[i][0], "HIT", "staccato",
                          " ".join(s[1] for s in sents[i:j])))
        i = max(j, i + 1)
    i = 0
    while i < len(sents) - 1:
        first = WORD.search(sents[i][1]).group().lower()
        j = i + 1
        while j < len(sents) and WORD.search(sents[j][1]).group().lower() == first:
            j += 1
        if j - i >= 2 and all(s[2] <= 10 for s in sents[i:j]):
            found.append((sents[i][0], "HIT" if j - i >= 3 else "hint",
                          "parallel_openers", " ".join(s[1] for s in sents[i:j])))
        i = j
    if len(sents) >= 4 and sents[-1][2] <= 8:
        found.append((sents[-1][0], "hint", "short_closer", sents[-1][1]))
    if text_words >= 40 and dashes and dashes * 100.0 / text_words > DASH_RATE:
        found.append((block[0][0], "hint", "em_dash_density",
                      "%d em dashes in %d words" % (dashes, text_words)))
    return found, text_words


def main(argv):
    skip = None
    if len(argv) > 2 and argv[1] == "--skip":
        skip = re.compile(argv[2])
        argv = argv[:1] + argv[3:]
    if len(argv) < 2:
        sys.stderr.write(__doc__)
        return 2
    cat = load_catalogue()
    hits = 0
    for path in argv[1:]:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        print("== %s" % path)
        for n, block in enumerate(blocks(lines, skip), 1):
            found, words = scan_block(block, cat)
            found = sorted(set((no, "HIT" if sev.lower() == "hit" else "hint", name, frag)
                               for no, sev, name, frag in found))
            nh = sum(1 for f in found if f[1] == "HIT")
            hits += nh
            print("-- block %d (lines %d-%d, %d words): %d HIT, %d hint"
                  % (n, block[0][0], block[-1][0], words, nh, len(found) - nh))
            for no, sev, name, frag in found:
                print("   %4d  %-4s %-17s | %s" % (no, sev, name, frag))
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
