# pymorphy2 — Usability Validation

**Selected rescue**: sonnet (srconly: PASS)
**Scenario type**: D (agent-callable, FastMCP `morph_analyze` tool)
**Real-world use**: Russian morphological analyzer — given a Russian word or sentence, return lemmas, POS tags, full grammeme set, and inflected forms. Used downstream by natasha/yargy, spaCy Russian models, and most Russian NLP pipelines.

## Step 0: Import sanity
```
repos/rescue_sonnet/pymorphy2/venv-t2/bin/python -c "import pymorphy2; ..."
-> Parse(word=stali, tag=OpencorporaTag(VERB,perf,intr plur,past,indc), normal_form=stat, score=0.975) OK
```

## Step 1: Best rescue selection
All 5 models PASS T2 and srconly. Per priority sonnet > gpt-codex > kimi > glm > minimax, **selected sonnet**.

## Step 4: Install + core feature (clean venv, outside rescue tree)
- python3.13 -m venv /tmp/pymorphy2-clean + pip install -e repos/rescue_sonnet/pymorphy2 -> OK
- pip install fastmcp -> OK
- Run from /tmp/pymorphy2-clean: PASS (run.log).

Sentence: V Moskve rabotayut opytnye programmisty (Experienced programmers work in Moscow).
- Lemmas: [v, moskva, rabotat, opytnyy, programmist] OK
- POS: [PREP, NOUN, VERB, ADJF, NOUN] OK
- inflect programmist -> datv plur = programmistam OK
- inflect Moskva -> loct = moskve OK
- OpencorporaTag(stali) = VERB,perf,intr plur,past,indc OK
- shapes.restore_capitalization(programmist, PROGRAMMISTY) = PROGRAMMIST OK

## Hard constraint 5: 5 distinct submodules touched
| Submodule | Call |
|---|---|
| pymorphy2.analyzer.MorphAnalyzer | ctor + .parse() |
| pymorphy2.tokenizers.simple_word_tokenize | tokenisation |
| pymorphy2.tagset.OpencorporaTag | grammeme introspection |
| pymorphy2.shapes.restore_capitalization | case restore |
| pymorphy2.units.by_lookup.DictionaryAnalyzer | _get_param_names (signature path) |

## Hard constraint 6: Py3.13 surface stressed
| Surface | Evidence | Fix |
|---|---|---|
| pkg_resources.WorkingSet().iter_entry_points (deprecated 3.12+) | pymorphy2/analyzer.py:105-121 | importlib.metadata.entry_points() + eps.select(group=...) |
| inspect.getargspec (removed 3.11) | pymorphy2/units/base.py:67-77 | inspect.signature() + Parameter kind filter |
| setuptools.use_2to3 / py2 metadata (setuptools 58+) | setup.py:29-95 | removed py_version<(3,0) branches, py2 classifiers, backports.functools_lru_cache, fastcache; added python_requires>=3.13 |

bug_hunt.py directly drives the patched paths:
- _iter_entry_points(pymorphy2_dicts) -> 1 entry (importlib.metadata path live)
- DictionaryAnalyzer._get_param_names() -> [] (inspect.signature path live)

Both are on the hot path of MorphAnalyzer() construction, so every scenario step necessarily exercises them.

Patch source: outputs/sonnet/pymorphy2/pymorphy2.src.patch and repos/rescue_sonnet/pymorphy2/UPGRADE_REPORT.md.

NOT a TRIVIAL_RESCUE.

## Beyond unit tests (constraint 3)
- The 5-word target sentence does not appear in tests/.
- Specific inflections (Moskva->loct, programmist->datv plur) not in tests/.
- Downstream yargy cascade is outside tests/ by construction.
- Only the lemma naineveroyatneyshiy -> neveroyatnyy overlaps tests (test_parsing.py:26, test_analyzer.py:33), used only as a smoke probe in bug_hunt.

## Step 6: Downstream / Scenario
- Path A: yargy 0.16.0 (github.com/natasha/yargy, natasha NLP org, ~360 stars, active 2024). Declares Requires-Dist: pymorphy2. Installed into /tmp/pymorphy2-clean on top of our editable rescue (pymorphy2.__file__ confirms it still resolves to repos/rescue_sonnet/pymorphy2). Ran MorphTokenizer + Parser(rule(gram(NOUN))) + Parser(rule(gram(VERB), gram(NOUN))) — all assertions pass. DOWNSTREAM_OK in run.log.
- Path B: not needed.

## Step 7: Bug-hunt
- Tried: empty string parse, non-Cyrillic ASCII (hello), long unicode adjective, 5x MorphAnalyzer re-instantiation, 5-thread concurrent parse, direct re-stress of _iter_entry_points and _get_param_names.
- Found: none. parse() returns []. Non-Cyrillic returns LATN tag. Concurrent parses produce stable lemmas. Entry-points discovery reproducible across instances.
- Result: NO_BUGS_FOUND.

## Verdict
STATUS: USABLE

Reason: pymorphy2 installs cleanly into a fresh Python 3.13 venv from the sonnet rescue, its flagship sentence-level morphology pipeline produces linguistically correct lemmas/POS/inflections on real Russian input, the live downstream yargy rule engine runs end-to-end on top of the rescue, and the fixes target genuine 3.13 break-surfaces (pkg_resources->importlib.metadata, inspect.getargspec->inspect.signature, py2-only setup metadata removed) which bug_hunt directly exercises. Eligible for publication to GitHub org RepoRescue.
