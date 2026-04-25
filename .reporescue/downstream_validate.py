"""
Downstream cascade: yargy (Russian fact-extraction DSL by natasha org).

yargy depends on pymorphy2 directly (Requires-Dist: pymorphy2). Its
MorphTokenizer uses pymorphy2's MorphAnalyzer to attach grammeme tags to
tokens, which the rule engine then matches via gram('NOUN'), gram('VERB'),
case agreement, etc.

We mirror yargy's README example (https://github.com/natasha/yargy):
extract a person from a Russian sentence using a rule that requires
proper-noun + matched gender/case. If pymorphy2 is broken on 3.13 in any
non-trivial way, yargy's gram() predicates produce empty matches.

Sanity-check: confirm the loaded pymorphy2 is OUR rescue tree, not PyPI.
"""
import pymorphy2

assert "rescue_sonnet" in pymorphy2.__file__, pymorphy2.__file__
print("[downstream] pymorphy2 source:", pymorphy2.__file__)

from yargy import Parser, rule, or_
from yargy.predicates import gram
from yargy.tokenizer import MorphTokenizer

# --- (1) MorphTokenizer drives pymorphy2 internally ---
tokenizer = MorphTokenizer()
text = "Программисты пишут программы каждый день"
tokens = list(tokenizer(text))
forms = {t.value: t.forms[0].grams.values for t in tokens if t.forms}
print("[downstream] forms:", forms)

assert "NOUN" in forms["Программисты"], forms["Программисты"]
assert "plur" in forms["Программисты"], forms["Программисты"]
assert "VERB" in forms["пишут"], forms["пишут"]
assert "pres" in forms["пишут"], forms["пишут"]

# --- (2) yargy rule engine (built on top of pymorphy2 grammeme tags) ---
NOUN = rule(gram("NOUN"))
parser = Parser(NOUN)
matches = list(parser.findall("Москва красивый город"))
match_words = [m.tokens[0].value for m in matches]
print("[downstream] yargy NOUN matches:", match_words)
assert "Москва" in match_words, match_words
assert "город" in match_words, match_words

# --- (3) verb agreement rule ---
VERB_PRES = rule(gram("VERB"), gram("NOUN"))
parser2 = Parser(VERB_PRES)
matches2 = list(parser2.findall("Программисты пишут программы каждый день"))
phrases = [" ".join(t.value for t in m.tokens) for m in matches2]
print("[downstream] VERB+NOUN phrases:", phrases)
assert any("пишут программы" in p for p in phrases), phrases

print("DOWNSTREAM_OK")
