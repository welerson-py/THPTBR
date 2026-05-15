"""Pre-generate TTS cache for common workshop phrases.

Translates each PT phrase to kreyol via NLLB, then synthesizes audio.
After this runs, those phrases (and their KR translations) hit instant cache.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from translate import pt_to_kr
from tts import synth_kreyol_wav_bytes

PHRASES_PT = [
    # Saudações / apresentação
    "Olá, tudo bem?",
    "Bom dia",
    "Boa tarde",
    "Boa noite",
    "Como você se chama?",
    "Qual é o seu nome?",
    "Meu nome é",
    "Prazer em conhecer você",
    "De onde você é?",
    "Você fala português?",
    "Eu não falo crioulo",
    "Vou te ajudar",
    "Vou te ensinar a usar o computador",
    # Computador básico
    "Aperte este botão",
    "Aperte o botão verde",
    "Aperte o botão vermelho",
    "Aperte o botão azul",
    "Clique aqui",
    "Clique com o mouse",
    "Use o mouse",
    "Mova o mouse",
    "Digite seu nome",
    "Digite a senha",
    "Abra o computador",
    "Ligue o computador",
    "Desligue o computador",
    "Feche o programa",
    "Abra o programa",
    "Salve o documento",
    "Apague isso",
    "Selecione com o mouse",
    "Arraste o ícone",
    # Pedidos / ajuda
    "Pode repetir, por favor?",
    "Eu não entendi",
    "Pode falar mais devagar?",
    "Espere um momento",
    "Tente de novo",
    "Vamos começar",
    "Já terminamos",
    "Faça assim",
    "Olhe a tela",
    # Confirmações
    "Sim",
    "Não",
    "Está certo",
    "Está errado",
    "Muito bem",
    "Obrigado",
    "Obrigada",
    "Por favor",
    "Desculpe",
    "Tudo bem",
    # Sequência
    "Primeiro",
    "Depois",
    "Agora",
    "Pronto",
    "Antes",
    "Continue",
    "Pare",
    # Comuns do dia
    "Você tem fome?",
    "Você tem sede?",
    "Quer água?",
    "Onde está o banheiro?",
    "Que horas são?",
    "Bom trabalho!",
]


def main():
    print(f"Pre-cachear {len(PHRASES_PT)} frases (PT -> KR -> TTS)...")
    print("Primeira frase carrega modelos (~30s), demais sao ~5-8s cada.\n", flush=True)
    t0 = time.time()
    ok = 0
    for i, pt in enumerate(PHRASES_PT, 1):
        try:
            t = time.time()
            kr = pt_to_kr(pt)
            wav = synth_kreyol_wav_bytes(kr)
            dt = time.time() - t
            ok += 1
            print(f"[{i:2d}/{len(PHRASES_PT)}] {dt:5.1f}s | PT: {pt[:40]:40s} | KR: {kr[:40]}", flush=True)
        except Exception as e:
            print(f"[{i:2d}/{len(PHRASES_PT)}] ERR: {e}", flush=True)
    print(f"\n[done] {ok}/{len(PHRASES_PT)} ok em {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
