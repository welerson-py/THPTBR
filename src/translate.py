"""Translate Haitian Creole to Portuguese with NLLB-200."""
from functools import lru_cache
import re

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from config import NLLB_MODEL, NLLB_SRC, NLLB_TGT


@lru_cache(maxsize=1)
def get_model():
    tok = AutoTokenizer.from_pretrained(NLLB_MODEL)
    tok.src_lang = NLLB_SRC
    model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    model.eval()
    return tok, model, tok.convert_tokens_to_ids(NLLB_TGT)


def _translate_chunk(text: str) -> str:
    tok, model, tgt_id = get_model()
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=256)
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


def translate(text: str) -> str:
    """Translate kreyol -> portuguese. Splits comma-separated word lists for accuracy."""
    text = text.strip()
    if not text:
        return ""
    # If many commas, treat as word list and translate each piece separately
    if text.count(",") >= 3:
        parts = [p.strip().strip(".") for p in re.split(r"[,;]", text) if p.strip()]
        return ", ".join(_translate_chunk(p) for p in parts if p)
    return _translate_chunk(text)
