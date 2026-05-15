"""Bidirectional translation kreyol <-> portugues via NLLB-200.
Manual overrides from correcoes.py take precedence over NLLB output."""
from functools import lru_cache
import re

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from config import NLLB_MODEL, NLLB_SRC, NLLB_TGT
from correcoes import get_pt_to_kr, get_kr_to_pt
from idiomas import aplicar_reescrita, get_cultural_kr


@lru_cache(maxsize=1)
def get_model():
    tok = AutoTokenizer.from_pretrained(NLLB_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    model.eval()
    return tok, model


def _translate_chunk(text: str, src_lang: str, tgt_lang: str) -> str:
    tok, model = get_model()
    tok.src_lang = src_lang
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=256)
    tgt_id = tok.convert_tokens_to_ids(tgt_lang)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=tgt_id,
            max_length=256,
            num_beams=2,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )
    return tok.decode(out[0], skip_special_tokens=True).strip()


def _translate(text: str, src_lang: str, tgt_lang: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.count(",") >= 3:
        parts = [p.strip().strip(".") for p in re.split(r"[,;]", text) if p.strip()]
        return ", ".join(_translate_chunk(p, src_lang, tgt_lang) for p in parts if p)
    return _translate_chunk(text, src_lang, tgt_lang)


def translate(text: str) -> str:
    """Kreyol -> Portuguese (default, used by batch pipeline)."""
    return _translate(text, NLLB_SRC, NLLB_TGT)


@lru_cache(maxsize=500)
def kr_to_pt(text: str) -> str:
    override = get_kr_to_pt(text)
    if override:
        return override
    return _translate(text, "hat_Latn", "por_Latn")


@lru_cache(maxsize=500)
def pt_to_kr(text: str) -> str:
    # Camada 1: override exato (correcoes.json)
    override = get_pt_to_kr(text)
    if override:
        return override
    # Camada 2: equivalente cultural direto (idiomas.IDIOMA_CULTURAL)
    cultural = get_cultural_kr(text)
    if cultural:
        return cultural
    # Camada 3: reescrita de idiomatismos antes de mandar pro NLLB
    rewritten = aplicar_reescrita(text)
    return _translate(rewritten, "por_Latn", "hat_Latn")
