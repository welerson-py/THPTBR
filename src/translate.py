"""Bidirectional translation kreyol <-> portugues via NLLB-200."""
from functools import lru_cache
import re

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from config import NLLB_MODEL, NLLB_SRC, NLLB_TGT


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


def kr_to_pt(text: str) -> str:
    return _translate(text, "hat_Latn", "por_Latn")


def pt_to_kr(text: str) -> str:
    return _translate(text, "por_Latn", "hat_Latn")
