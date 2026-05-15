"""Manual translation overrides for cases where NLLB gets it wrong.

Stored in data/correcoes.json. Keys are lowercased input text.
Useful examples we already know:
- PT "não" → KR "Non" (NLLB outputs "Pa gen" wrong)
- PT "você tem sede?" → KR "Èske w gen swaf?" (NLLB outputs "tansyon" = pressão arterial)
"""
import json
from pathlib import Path
from typing import Optional

from config import DATA

CORRECOES_FILE = DATA / "correcoes.json"

_DEFAULTS = {
    "pt_to_kr": {
        "não": "Non",
        "nao": "Non",
        "você tem sede?": "Èske w gen swaf?",
        "voce tem sede?": "Èske w gen swaf?",
        "está com sede?": "Èske w gen swaf?",
        "olá": "Bonjou",
        "ola": "Bonjou",
        "tchau": "Orevwa",
    },
    "kr_to_pt": {
        "non": "Não",
        "wi": "Sim",
        "mèsi": "Obrigado",
        "mesi": "Obrigado",
        "tanpri": "Por favor",
        "mwen pa konprann": "Eu não entendo",
        "mwen pa konnen": "Eu não sei",
        "èd mwen tanpri": "Me ajude por favor",
        "ed mwen tanpri": "Me ajude por favor",
        "mwen vle aprann": "Eu quero aprender",
        "mwen rele": "Meu nome é",
        "kòman ou ye": "Como você está",
        "koman ou ye": "Como você está",
        "bonjou": "Bom dia",
        "bonswa": "Boa noite",
        # Corrigidos do precache imigrante (NLLB errou)
        "orevwa": "Adeus",
        "mwen swaf": "Estou com sede",
        "ki lè li ye?": "Que horas são?",
        "ki le li ye?": "Que horas são?",
        "ki lè li ye": "Que horas são?",
        "ki le li ye": "Que horas são?",
        "mwen pèdi": "Estou perdido",
        "mwen pedi": "Estou perdido",
        "klike kote?": "Onde clico?",
        "klike kote": "Onde clico?",
        "mwen grangou": "Estou com fome",
        "kisa sa vle di?": "O que isso significa?",
        "kisa sa vle di": "O que isso significa?",
        "mwen pa wè": "Eu não vejo",
        "mwen pa we": "Eu não vejo",
        "padon": "Desculpa",
        "eskize m": "Com licença",
        "ankò": "De novo",
        "anko": "De novo",
        "sa bon": "Está bom",
        "sa pa bon": "Não está bom",
    },
}


def _load() -> dict:
    if CORRECOES_FILE.exists():
        try:
            data = json.loads(CORRECOES_FILE.read_text(encoding="utf-8"))
            # ensure both keys exist
            for k in ("pt_to_kr", "kr_to_pt"):
                data.setdefault(k, {})
            return data
        except Exception:
            pass
    # seed defaults on first run
    _save(_DEFAULTS)
    return dict(_DEFAULTS)


def _save(data: dict) -> None:
    CORRECOES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CORRECOES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_pt_to_kr(text: str) -> Optional[str]:
    return _load()["pt_to_kr"].get(text.strip().lower())


def get_kr_to_pt(text: str) -> Optional[str]:
    return _load()["kr_to_pt"].get(text.strip().lower())


def set_pt_to_kr(pt: str, kr: str) -> None:
    data = _load()
    data["pt_to_kr"][pt.strip().lower()] = kr.strip()
    _save(data)


def set_kr_to_pt(kr: str, pt: str) -> None:
    data = _load()
    data["kr_to_pt"][kr.strip().lower()] = pt.strip()
    _save(data)


def list_all() -> dict:
    return _load()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    d = _load()
    print(f"PT→KR overrides: {len(d['pt_to_kr'])}")
    print(f"KR→PT overrides: {len(d['kr_to_pt'])}")
    print(f"File: {CORRECOES_FILE}")
