"""
pymorphy2 usability validation — D-type scenario (FastMCP agent-callable).

Real use case: Russian morphological analysis. We analyse a real Russian
sentence end-to-end: tokenise -> parse each word -> extract lemmas and POS ->
inflect a noun into another grammatical case.

Hard constraints:
  1 Real input: real Russian sentence (not mock/empty).
  2 Real output assertion: assert lemmas, POS tags, and inflected forms
    against linguistically correct ground truth.
  3 Beyond unit tests: this exact 6-word sentence + the inflection chain are
    NOT in tests/ (grep proves it).
  4 Primary use mode: full sentence-level morphology = pymorphy2's flagship.
  5 Three distinct submodules: pymorphy2.analyzer (MorphAnalyzer),
    pymorphy2.tokenizers (simple_word_tokenize), pymorphy2.shapes
    (restore_capitalization), pymorphy2.tagset (OpencorporaTag).
  6 Stresses 3.13 surface: MorphAnalyzer() ctor walks _iter_entry_points()
    (pkg_resources->importlib.metadata) and unit registry calls
    _get_param_names (inspect.getargspec->inspect.signature).
"""
import asyncio
import sys
from fastmcp import FastMCP, Client

mcp = FastMCP("pymorphy2-validate")


@mcp.tool
def morph_analyze(sentence: str) -> dict:
    """Tokenise a Russian sentence, parse each word, return lemmas + tags."""
    import pymorphy2
    from pymorphy2.tokenizers import simple_word_tokenize

    morph = pymorphy2.MorphAnalyzer()
    tokens = simple_word_tokenize(sentence)
    parses = []
    for tok in tokens:
        p = morph.parse(tok)[0]
        parses.append({
            "token": tok,
            "lemma": p.normal_form,
            "pos": p.tag.POS,
            "tag": str(p.tag),
        })
    return {"tokens": tokens, "parses": parses}


async def main():
    sentence = "В Москве работают опытные программисты"
    # Russian: "Experienced programmers work in Moscow"
    # Expected lemmas: в, москва, работать, опытный, программист
    # Expected POS:   PREP, NOUN,    VERB,      ADJF,    NOUN

    async with Client(mcp) as c:
        out = await c.call_tool("morph_analyze", {"sentence": sentence})
        data = out.data
        print("[1] Tool returned tokens:", data["tokens"])

        assert data["tokens"] == [
            "В", "Москве", "работают", "опытные", "программисты"
        ], data["tokens"]

        lemmas = [p["lemma"] for p in data["parses"]]
        poses = [p["pos"] for p in data["parses"]]
        print("[1] Lemmas:", lemmas)
        print("[1] POS:   ", poses)

        # Linguistic ground truth
        assert lemmas == ["в", "москва", "работать", "опытный", "программист"], lemmas
        assert poses == ["PREP", "NOUN", "VERB", "ADJF", "NOUN"], poses

    # ---------- submodule path 2: tagset.OpencorporaTag introspection ----------
    import pymorphy2
    from pymorphy2.tagset import OpencorporaTag
    morph = pymorphy2.MorphAnalyzer()
    p = morph.parse("стали")[0]  # ambiguous: noun "сталь" or verb "стать"
    tag = p.tag
    assert isinstance(tag, OpencorporaTag), type(tag)
    # "стали" top parse should be VERB (past, plural)
    assert tag.POS == "VERB", tag.POS
    assert "past" in tag, tag
    assert "plur" in tag, tag
    print("[2] OpencorporaTag introspection on 'стали' OK:", tag)

    # ---------- submodule path 3: shapes.restore_capitalization ----------
    from pymorphy2.shapes import restore_capitalization
    # restore casing of a lemma to match how the original word was capitalised
    assert restore_capitalization("москва", "Москве") == "Москва"
    assert restore_capitalization("программист", "ПРОГРАММИСТЫ") == "ПРОГРАММИСТ"
    print("[3] shapes.restore_capitalization OK")

    # ---------- submodule path 4: real inflection (the flagship feature) ----
    # Take "программист" (nom sg) -> inflect to dative plural "программистам"
    # Take "москва" (nom) -> inflect to prepositional case "москве"
    prog = morph.parse("программист")[0]
    datp = prog.inflect({"datv", "plur"})
    assert datp is not None, "inflect returned None"
    assert datp.word == "программистам", datp.word
    print("[4] inflect программист -> datv plur =", datp.word)

    msk = morph.parse("Москва")[0]
    loct = msk.inflect({"loct"})
    assert loct is not None
    assert loct.word.lower() == "москве", loct.word
    print("[4] inflect Москва -> loct =", loct.word)

    print("USABLE")


if __name__ == "__main__":
    asyncio.run(main())
