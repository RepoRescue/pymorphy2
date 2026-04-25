# pymorphy2 (RepoRescue Modernized)

**Morphological analyzer for Russian and Ukrainian.** Given a surface word form, it returns the lemma (dictionary base form), POS, the full grammeme set (number, case, tense, aspect, person, ...), and supports inverse inflection (bending a word into a target case / number / tense).

Academic identity: **Korobov, M. — Morphological Analyzer and Generator for Russian and Ukrainian Languages**, AIST 2015 (Springer CCIS vol. 542, pp. 320–332). A widely cited open-source tool in the Russian NLP community.

Downstream ecosystem: the natasha-NLP family (`yargy` rule engine, `natasha` named-entity recognizer) depends on `pymorphy2` directly; spaCy Russian, LanguageTool's Russian rules, and a long tail of Russian information-extraction pipelines all build on top of it.

> **Modernized for Python 3.13** — the upstream version crashes on `import pymorphy2` under Python 3.13. This repository is the source-only output of the RepoRescue benchmark after a Sonnet rescue plus real-world usability validation (`STATUS: USABLE`).

---

## Install

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -e .
pip install pymorphy2-dicts-ru   # Russian dictionary data; for Ukrainian, install -uk instead
```

## Quick start — analyzing a real Russian sentence

```python
import pymorphy2
from pymorphy2.tokenizers import simple_word_tokenize

morph = pymorphy2.MorphAnalyzer()
sentence = "В Москве работают опытные программисты"   # "Experienced programmers work in Moscow"

for tok in simple_word_tokenize(sentence):
    p = morph.parse(tok)[0]
    print(f"{tok:14s} lemma={p.normal_form:12s} POS={p.tag.POS}")

# В              lemma=в            POS=PREP
# Москве         lemma=москва       POS=NOUN
# работают       lemma=работать     POS=VERB
# опытные        lemma=опытный      POS=ADJF
# программисты   lemma=программист  POS=NOUN

# Ambiguity + introspection
p = morph.parse("стали")[0]          # homonym: noun "сталь" (steel) or verb "стать" (to become)
assert p.normal_form == "стать" and p.tag.POS == "VERB"
assert "past" in p.tag and "plur" in p.tag

# Inflection (the flagship feature): bend "программист" into the dative plural
prog = morph.parse("программист")[0]
assert prog.inflect({"datv", "plur"}).word == "программистам"
```

---

## What was fixed (for Python 3.13)

The upstream version had three real break points on Python 3.13, all on the hot path of `MorphAnalyzer()` construction — every call site triggers them:

| Failure surface | Location | Fix |
|---|---|---|
| `pkg_resources.WorkingSet().iter_entry_points(...)` (deprecated in 3.12+, setuptools resolution behavior changed on 3.13) | `pymorphy2/analyzer.py:105-121` | Switched to `importlib.metadata.entry_points().select(group=...)` (standard API since Python 3.10) |
| `inspect.getargspec(...)` (removed in 3.11) | `pymorphy2/units/base.py:67-77` | Switched to `inspect.signature()` plus `Parameter.kind` filtering for positional arguments |
| `setup.py: use_2to3=True` and Py2-only metadata for `backports.functools_lru_cache` / `fastcache` (rejected by setuptools 58+) | `setup.py:29-95` | Removed the `py_version<(3,0)` branches and Py2 classifiers; added `python_requires=">=3.13"` |

Evidence: see `outputs/sonnet/pymorphy2/pymorphy2.src.patch` and `repos/rescue_sonnet/pymorphy2/UPGRADE_REPORT.md`.

---

## Downstream cascade unlock — the highlight of this rescue

Fixing `pymorphy2` is not just about making `import` succeed; it **brings the entire Russian NLP toolchain back to life on Python 3.13**. We validate this end-to-end against the upstream `yargy` (natasha-NLP org, ~360 stars, still maintained in 2024, declares `Requires-Dist: pymorphy2`):

```bash
pip install yargy
python .reporescue/downstream_validate.py
```

The script:
1. Asserts that `pymorphy2.__file__` resolves to **this rescue tree** (not a stale PyPI install);
2. Lets `yargy.tokenizer.MorphTokenizer` inject `pymorphy2` grammeme tags into tokens;
3. Runs `Parser(rule(gram("NOUN")))` against `"Москва красивый город"`, requiring it to extract `Москва` and `город`;
4. Runs `Parser(rule(gram("VERB"), gram("NOUN")))` against `"Программисты пишут программы каждый день"`, requiring it to match the `пишут программы` phrase.

Expected output: `DOWNSTREAM_OK`. This is one of the four cascade-unlock entries that pass across the entire RepoRescue Python set.

---

## Usability validation summary

| Check | Result |
|---|---|
| Clean venv install (Python 3.13) | OK |
| Flagship features (sentence-level lemma / POS / inflection) | OK — produces linguistically correct output on real Russian sentences |
| Five independent submodules exercised concurrently (`analyzer` / `tokenizers` / `tagset` / `shapes` / `units.by_lookup`) | OK |
| Bug-hunt: empty string / non-Cyrillic input / 5x `MorphAnalyzer` re-instantiation / 5-thread concurrent parse / direct re-stress of `_iter_entry_points` and `_get_param_names` | **NO_BUGS_FOUND** |
| Downstream cascade (`yargy` rule engine) | OK |

Full report in `REPORT.md`; runnable scripts in `usability_validate.py`, `downstream_validate.py`, `bug_hunt.py`.

---

## Disclaimer

This is a release produced by the [RepoRescue benchmark](https://github.com/RepoRescue) — AI-driven automated repair followed by offline manual validation. **It is not an official fork of the upstream `kmike/pymorphy2`.** We have validated only the morphological core API and the downstream cascade described above under Python 3.13 with current dependencies; we have not covered every corner case of the upstream repository. Please test your critical paths before relying on this in production.

If you come from the natasha / yargy / spaCy-ru ecosystem and want `pymorphy2` to run again on 3.13, this version is a working starting point.

## License

MIT (inherited from upstream). Please preserve the academic citation:

```
Korobov M. Morphological Analyzer and Generator for Russian and Ukrainian Languages.
In: Analysis of Images, Social Networks and Texts (AIST 2015), pp. 320–332.
```

```
RepoRescue (2026). Modernizing abandoned Python repositories for Python 3.13.
https://github.com/RepoRescue
```
