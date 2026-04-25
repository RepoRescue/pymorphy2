"""
Step 7 — anti-PyCG-blindspot probes for pymorphy2.

Targets:
- Boundary inputs: empty / non-Cyrillic / mixed scripts / huge words.
- State leak across repeated MorphAnalyzer construction (entry_points cache).
- Concurrent parse from multiple threads.
- 3.13 surface re-stress: explicitly walk _iter_entry_points and _get_param_names.
"""
import threading
import pymorphy2

bugs = []
morph = pymorphy2.MorphAnalyzer()

# --- 1. Empty + edge inputs ---
try:
    r = morph.parse("")
    if not isinstance(r, list):
        bugs.append(f"empty parse returned {type(r)}")
except Exception as e:
    bugs.append(f"empty parse raised: {e!r}")

# --- 2. Non-Cyrillic ---
r = morph.parse("hello")
assert isinstance(r, list) and len(r) >= 1
print("[hunt] non-cyrillic 'hello' parsed: tag=", r[0].tag)

# --- 3. Long unicode noun chain ---
long_word = "наиневероятнейшего"
r = morph.parse(long_word)
print(f"[hunt] long word lemma: {r[0].normal_form}")

# --- 4. Re-instantiate MorphAnalyzer many times (entry_points re-discovery) ---
for i in range(5):
    m = pymorphy2.MorphAnalyzer()
    p = m.parse("кот")[0]
    assert p.normal_form == "кот", (i, p)
print("[hunt] 5x re-instantiation OK")

# --- 5. Concurrent parse from threads ---
results = []
def worker(word):
    p = morph.parse(word)[0]
    results.append((word, p.normal_form))
threads = [threading.Thread(target=worker, args=(w,))
           for w in ["программист", "Москва", "работают", "опытные", "стали"]]
for t in threads: t.start()
for t in threads: t.join()
print("[hunt] concurrent results:", results)
assert len(results) == 5

# --- 6. Re-stress 3.13 fix: directly call patched function ---
from pymorphy2.analyzer import _iter_entry_points
eps = list(_iter_entry_points("pymorphy2_dicts"))
print(f"[hunt] _iter_entry_points('pymorphy2_dicts') -> {len(eps)} entries (importlib.metadata path)")
assert len(eps) >= 1, "no entry points found — pkg_resources->importlib.metadata fix may have regressed"

# --- 7. Re-stress getargspec->signature fix ---
from pymorphy2.units.base import BaseAnalyzerUnit
# Pick a real subclass and walk _get_param_names
from pymorphy2.units.by_lookup import DictionaryAnalyzer
params = DictionaryAnalyzer._get_param_names()
print(f"[hunt] DictionaryAnalyzer._get_param_names() = {params} (inspect.signature path)")
assert isinstance(params, list)

if bugs:
    print("BUGS_FOUND:", bugs)
else:
    print("NO_BUGS_FOUND")
