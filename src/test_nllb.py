"""Test NLLB-200 translation from Haitian Creole -> Portuguese."""
import sys
import json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

MODEL = "facebook/nllb-200-distilled-600M"

print(f"Loading {MODEL}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL, torch_dtype=torch.float32)
model.eval()

# Real segments from the Whisper kreyol transcription
samples = [
    "N'en video sa n'o par la plan keg feb en potige.",
    "Fe, faser, manje, komer, boe, beber, maché, kaminyar, shita, sentar, uite, ficar,",
    "ali, ir, ashti, komprar, van, vendir, travai, trabalar, pali, falar, vaip, dar,",
    "prete, emprestar, uithke, arriskar, tuné, voltar, blece, machukar, pote ali, levar, potevini,",
    "trazeer, mande, perguntar, priye, rezar, mete, kolokar, komase, komesar, fini,",
]

tokenizer.src_lang = "hat_Latn"
target_lang_id = tokenizer.convert_tokens_to_ids("por_Latn")

for text in samples:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=256,
            num_beams=2,
        )
    pt = tokenizer.decode(out[0], skip_special_tokens=True)
    print(f"\nKR: {text}")
    print(f"PT: {pt}")
