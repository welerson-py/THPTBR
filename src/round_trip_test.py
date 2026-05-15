"""Round-trip test: TTS kreyol → MMS transcription → NLLB to PT.

Validates the WHOLE immigrant pipeline without needing a real Haitian speaker.
If round-trip preserves meaning, MMS + NLLB are doing their jobs on synthesized audio.
Real speech may still differ but this catches systemic problems."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tts import synth_kreyol
from transcribe_mms import transcribe_audio_array
from translate import kr_to_pt

# Real things an immigrant would likely say in a workshop
PHRASES_KR = [
    ("Mwen pa konprann", "Eu não entendo"),
    ("Èske w ka repete tanpri?", "Pode repetir por favor?"),
    ("Mwen vle aprann", "Eu quero aprender"),
    ("Kijan yo di sa nan pòtigè?", "Como se diz isso em português?"),
    ("Èd mwen tanpri", "Me ajude por favor"),
    ("Mwen pèdi", "Estou perdido"),
    ("Klike kote?", "Clico onde?"),
    ("Mwen rele Pyè", "Meu nome é Pierre"),
    ("Mwen grangou", "Estou com fome"),
    ("Mèsi anpil", "Muito obrigado"),
    ("Bonjou kijan ou ye?", "Bom dia como você está?"),
    ("Ki kote twalèt la ye?", "Onde está o banheiro?"),
]


def main():
    print(f"Testando round-trip em {len(PHRASES_KR)} frases kreyol...\n", flush=True)
    matches = 0
    for i, (kr_orig, pt_expected) in enumerate(PHRASES_KR, 1):
        print(f"[{i:2d}] Original KR: {kr_orig}", flush=True)
        print(f"     Esperado PT: {pt_expected}", flush=True)
        try:
            t = time.time()
            audio, sr = synth_kreyol(kr_orig)
            t_tts = time.time() - t

            t = time.time()
            kr_back = transcribe_audio_array(audio)
            t_mms = time.time() - t

            t = time.time()
            pt = kr_to_pt(kr_back) if kr_back else ""
            t_nllb = time.time() - t

            print(f"     MMS leu:     {kr_back}", flush=True)
            print(f"     NLLB -> PT:  {pt}", flush=True)
            print(f"     Tempos: TTS={t_tts:.1f}s | MMS={t_mms:.1f}s | NLLB={t_nllb:.1f}s", flush=True)
            if pt_expected.lower().split()[0] in pt.lower() or pt.lower().split()[0:1] == pt_expected.lower().split()[0:1]:
                print(f"     ✓ semantica preservada", flush=True)
                matches += 1
            else:
                print(f"     ✗ divergente", flush=True)
        except Exception as e:
            print(f"     ERR: {e}", flush=True)
        print(flush=True)

    print(f"\n[done] {matches}/{len(PHRASES_KR)} frases com semantica preservada")


if __name__ == "__main__":
    main()
