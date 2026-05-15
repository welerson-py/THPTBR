"""Dicionário de idiomatismos BR + equivalentes culturais em kreyòl.

Estrutura de 2 camadas:

1. IDIOMA_REWRITES: PT idiomático -> PT literal (substring match dentro de frase maior).
   Aplicado ANTES de mandar pro NLLB.
   Ex: "esse exercício é mamão com açúcar" -> "esse exercício é muito fácil"

2. IDIOMA_CULTURAL: PT idiomático -> KR cultural (match exato, frase isolada).
   Sobrescreve totalmente, NLLB não roda.
   Ex: "mamão com açúcar" -> "se dlo kòk"

Todo lookup ignora acentos — brasileiro digitando/transcrevendo nao usa acento
todas as vezes (Whisper as vezes tambem perde acento).
"""
import re
import unicodedata
from typing import Optional


def _strip_accents(s: str) -> str:
    """Remove acentos e baixa caixa, pra normalizar lookups."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()

# ============================================================
# 1. REESCRITA IDIOMATICA -> PT LITERAL
# ============================================================
# Aplicado antes do NLLB pra "limpar" gírias e expressões.
# Chave: idiomatismo em PT, Valor: equivalente literal em PT.

IDIOMA_REWRITES = {
    # --- Facilidade / dificuldade ---
    "mamão com açúcar": "muito fácil",
    "mamao com acucar": "muito fácil",
    "barbada": "muito fácil",
    "moleza": "muito fácil",
    "sopa no mel": "muito fácil",
    "pepino": "problema",
    "abacaxi": "problema difícil",
    "fogo no rabo": "urgência",

    # --- Resolver / fazer ---
    "dar um jeito": "resolver",
    "dar um jeitinho": "resolver",
    "quebrar um galho": "ajudar",
    "dar uma força": "ajudar",
    "dar uma mão": "ajudar",
    "se virar": "se arranjar",
    "se vira": "se arranja",
    "ir na fé": "tentar com confiança",
    "matar a charada": "descobrir",
    "tirar de letra": "fazer fácil",

    # --- Falhar / errar ---
    "ficar na mão": "ficar sem ajuda",
    "ficou na mão": "ficou sem ajuda",
    "fiquei na mão": "fiquei sem ajuda",
    "pisar na bola": "errar",
    "pisou na bola": "errou",
    "pisei na bola": "errei",
    "dar com os burros n'água": "falhar",
    "se dar mal": "dar errado",
    "queimar o filme": "perder a reputação",
    "vacilar": "errar",
    "vacilei": "errei",
    "vacilou": "errou",

    # --- Aborrecer ---
    "encher o saco": "incomodar",
    "saco cheio": "cansado de aguentar",
    "tô de saco cheio": "estou cansado",
    "encheu o saco": "incomodou demais",
    "está de mal humor": "está irritado",
    "tô bolado": "estou irritado",

    # --- Confirmação / acordo ---
    "fechado": "combinado",
    "fechou": "combinado",
    "tá ligado": "você entendeu",
    "tá ligado?": "está entendendo?",
    "tô ligado": "eu entendi",
    "beleza": "está bem",
    "blz": "está bem",
    "tranquilo": "está bem",
    "de boa": "tudo bem",
    "tá de boa": "está tudo bem",
    "show": "muito bom",
    "show de bola": "muito bom",
    "valeu": "obrigado",
    "vlw": "obrigado",
    "demorou": "claro",

    # --- Estado / sentimento ---
    "tô na pista": "estou pronto",
    "tô na correria": "estou ocupado",
    "tô na luta": "estou trabalhando duro",
    "fica tranquilo": "fique calmo",
    "fica frio": "fique calmo",
    "relaxa": "fique calmo",
    "vai dar tudo certo": "tudo vai funcionar bem",
    "tá tudo certo": "está tudo bem",
    "tô numa boa": "estou bem",

    # --- Workshop / instrução comum ---
    "presta atenção": "preste atenção",
    "olha aqui": "olhe aqui",
    "olha só": "veja",
    "saca?": "entende?",
    "sacou?": "entendeu?",
    "manjou?": "entendeu?",
    "manja disso?": "sabe disso?",
    "pega a visão": "compreende",
    "tô explicando": "estou explicando",
    "vou te mostrar": "vou te mostrar",
    "presta atenção aqui": "preste atenção aqui",

    # --- Cumprimentos / despedidas ---
    "e aí": "olá",
    "fala aí": "olá",
    "salve": "olá",
    "até mais": "até logo",
    "falou": "tchau",
    "flw": "tchau",

    # --- Diminutivos típicos ---
    "minutinho": "minuto",
    "rapidinho": "rápido",
    "agorinha": "agora",
    "pouquinho": "pouco",
    "comidinha": "comida",
    "cafezinho": "café",

    # --- Gauchismos / regionalismos do Sul ---
    "tri bom": "muito bom",
    "tri legal": "muito legal",
    "tri bem": "muito bem",
    "bah": "puxa",
    "bah tchê": "puxa",
    "tchê": "cara",
    # nota: removido "fresqueia" — em RS tem tom de briga, nao acolhedor
    "feito o carreto": "terminamos",
    "barbaridade": "incrível",
    "negada": "pessoal",
    "guri": "menino",
    "guria": "menina",
    "guarida": "abrigo",
    "vivendo na fronteira": "perto de outro país",
    "tropeço": "erro",
    "topete": "ousadia",

    # --- Outros comuns ---
    "ué": "",  # interjeição sem tradução
    "né": "não é",
    "tá": "está",
    "tô": "estou",
    "pra": "para",
    "pro": "para o",
    "pô": "puxa",
    "nossa": "puxa",
    "caraca": "puxa",
    "ih": "",
}


# ============================================================
# 2. EQUIVALENTES CULTURAIS DIRETOS (PT -> KR cultural)
# ============================================================
# Quando a frase é APENAS o idiomatismo, sobrescreve direto no kreyòl real.
# Não passa por NLLB.

IDIOMA_CULTURAL = {
    # Facilidade
    "mamão com açúcar": "Se dlo kòk",
    "mamao com acucar": "Se dlo kòk",
    "é mamão com açúcar": "Se dlo kòk",
    "é uma barbada": "Se dlo kòk",
    "barbada": "Fasil anpil",
    "moleza": "Fasil anpil",
    "é moleza": "Se fasil anpil",

    # Problema
    "abacaxi": "Yon pwoblèm",
    "é um abacaxi": "Se yon pwoblèm",
    "pepino": "Yon pwoblèm",

    # Resolver
    "dar um jeito": "Degaje m",
    "vou dar um jeito": "M ap degaje m",
    "dá um jeito": "Degaje w",
    "quebrar um galho": "Ede yon ti kras",
    "se vira": "Degaje w",

    # Estado
    "ficar na mão": "Rete bloke",
    "fiquei na mão": "M rete bloke",
    "tudo bem": "Tout bagay anfòm",
    "tudo certo": "Tout bagay anfòm",
    "tudo tranquilo": "Tout bagay anfòm",

    # Concordância
    "fechado": "Dakò",
    "fechou": "Dakò",
    "beleza": "Dakò",
    "tá bom": "Dakò",
    "tá certo": "Sa kòrèk",

    # Cumprimentos casuais
    "e aí": "Sak pase",
    "e aí?": "Sak pase?",
    "fala aí": "Pale ave m",
    "valeu": "Mèsi",
    "valeu!": "Mèsi!",

    # Despedidas
    "tchau": "Orevwa",
    "até mais": "N a wè pita",
    "falou": "Orevwa",

    # ============================================================
    # CALOR DE OFICINA: acolhimento, incentivo, celebração
    # ============================================================
    # Sucesso / celebração
    "muito bem você conseguiu": "Ala bèl sa bèl, ou reyalize l!",
    "muito bem voce conseguiu": "Ala bèl sa bèl, ou reyalize l!",
    "tri bom você conseguiu": "Ala bèl sa bèl, ou reyalize l!",
    "tri bom voce conseguiu": "Ala bèl sa bèl, ou reyalize l!",
    "parabéns": "Konpliman!",
    "parabens": "Konpliman!",
    "parabéns você conseguiu": "Konpliman! Ou reyalize l!",
    "parabens voce conseguiu": "Konpliman! Ou reyalize l!",
    "você é demais": "Ou ekstraòdinè!",
    "voce e demais": "Ou ekstraòdinè!",
    "você está indo bem": "Ou ap mache byen anpil",
    "voce esta indo bem": "Ou ap mache byen anpil",

    # Incentivo / acolhimento
    "não desiste": "Pa janm dekouraje",
    "nao desiste": "Pa janm dekouraje",
    "não desista": "Pa janm dekouraje",
    "nao desista": "Pa janm dekouraje",
    "tenta de novo": "Eseye ankò",
    "tenta de novo eu tô com você": "Eseye ankò, mwen avèk ou",
    "tenta de novo eu to com voce": "Eseye ankò, mwen avèk ou",
    "fica tranquilo tenta de novo": "Pa enkyete w, eseye ankò",
    "fica tranquila tenta de novo": "Pa enkyete w, eseye ankò",
    "fica tranquilo vai dar certo": "Pa enkyete w, tout bagay ap mache byen",
    "vai dar tudo certo": "Tout bagay ap mache byen",
    "estamos juntos": "Nou ansanm",
    "vamos juntos": "Annou ansanm",
    "tô com você": "M la avèk ou",
    "to com voce": "M la avèk ou",
    "estou com você": "M la avèk ou",
    "estou aqui": "Mwen la avèk ou",
    "calma": "Pa enkyete w",
    "fica calmo": "Pa enkyete w",

    # Finalização carinhosa
    "feito o carreto": "Travay la fini, nou fè yon bèl travay!",
    "terminamos": "Travay la fini, nou fè yon bèl travay!",
    "acabamos": "Travay la fini, nou fè yon bèl travay!",
    "missão cumprida": "Misyon akonpli!",
    "missao cumprida": "Misyon akonpli!",

    # Boas-vindas
    "bem-vindo": "Byenvini lakay nou",
    "bem vindo": "Byenvini lakay nou",
    "seja bem-vindo": "Byenvini lakay nou",
    "seja bem vindo": "Byenvini lakay nou",
    "estamos felizes de ter você aqui": "Nou kontan ou la avèk nou",

    # ============================================================
    # EXPANSAO: girias diarias haitianas pra "sentir em casa"
    # ============================================================
    # Cumprimentos super comuns no Haiti
    "tudo bem": "Tout bagay anfòm",
    "tudo bom": "Tout bagay anfòm",
    "tudo certo": "Tout bagay anfòm",
    "como vai": "Sa k pase?",
    "como vai?": "Sa k pase?",
    "e aí": "Sa k pase?",
    "e aí?": "Sa k pase?",
    "como você está": "Kòman ou ye?",
    "como você está?": "Kòman ou ye?",
    "tô bem": "M la",
    "estou bem": "M la",
    "tô na boa": "N ap boule",
    "tô na minha": "N ap boule",
    "tô tranquilo": "Kè m poze",
    "estou tranquilo": "Kè m poze",
    "tô em paz": "Mwen anpè",

    # Saudacoes por horario
    "bom dia": "Bonjou",
    "boa tarde": "Bon apremidi",
    "boa noite": "Bon swa",
    "boa madrugada": "Bon nwit",

    # Despedidas
    "tchau tchau": "Orevwa",
    "até amanhã": "Demen",
    "ate amanha": "Demen",
    "até logo": "N a wè pita",
    "ate logo": "N a wè pita",
    "até a próxima": "N a wè pita",
    "ate a proxima": "N a wè pita",
    "boa semana": "Bon semèn",
    "bom fim de semana": "Bon wikenn",

    # Acolhimento profundo
    "pode contar comigo": "Konte sou mwen",
    "tô aqui pra ajudar": "Mwen la pou m ede w",
    "estou aqui pra ajudar": "Mwen la pou m ede w",
    "tô aqui": "Mwen la",
    "estou aqui": "Mwen la",
    "tô junto": "Mwen avèk ou",
    "to junto": "Mwen avèk ou",
    "tô contigo": "Mwen avèk ou",
    "to contigo": "Mwen avèk ou",
    "tô do seu lado": "M sou kote w",
    "estou do seu lado": "M sou kote w",

    # Quando o aluno erra (reduzir vergonha)
    "tudo bem errar": "Pa gen pwoblèm si w fè erè",
    "errar é normal": "Sa nòmal pou fè erè",
    "todo mundo erra": "Sa rive tout moun",
    "acontece com todo mundo": "Sa rive tout moun",
    "não é nada": "Sa pa anyen",
    "nao e nada": "Sa pa anyen",
    "não foi nada": "Sa pa anyen",
    "sem problema": "Pa gen pwoblèm",
    "sem problemas": "Pa gen pwoblèm",
    "não tem problema": "Pa gen pwoblèm",
    "nao tem problema": "Pa gen pwoblèm",
    "tudo bem isso": "Pa gen pwoblèm",

    # Pedidos de calma
    "calma": "Kè poze",
    "respira": "Pran yon souf",
    "respira fundo": "Pran yon souf pwofon",
    "vai com calma": "Pran tan ou",
    "sem pressa": "Pran tan ou",
    "tem tempo": "Ou gen tan",

    # Incentivo direto
    "você consegue": "Ou ka fè l",
    "voce consegue": "Ou ka fè l",
    "você é capaz": "Ou kapab",
    "voce e capaz": "Ou kapab",
    "acredito em você": "M kwè nan ou",
    "acredito em voce": "M kwè nan ou",
    "vai conseguir": "W ap reyisi",
    "você vai conseguir": "W ap reyisi",
    "voce vai conseguir": "W ap reyisi",
    "não desanima": "Pa dekouraje",
    "nao desanima": "Pa dekouraje",
    "não desanime": "Pa dekouraje",
    "vamos lá": "Annou",
    "vamos la": "Annou",
    "bora": "Annou",
    "bora lá": "Annou ale",
    "bora la": "Annou ale",
    "vai lá": "Ale",

    # Sucesso (varias formas brasileiras de elogiar)
    "muito bom": "Trè bon",
    "muito bem": "Bravo",
    "boa": "Bravo",
    "boa!": "Bravo!",
    "isso aí": "Sa a, se sa!",
    "isso ai": "Sa a, se sa!",
    "isso mesmo": "Egzatman",
    "exato": "Egzatman",
    "perfeito": "Pafè",
    "show": "Ekstraòdinè",
    "show de bola": "Ekstraòdinè",
    "demais": "Bèl anpil",
    "arrasou": "Ou kraze l",
    "mandou bem": "Ou fè byen",
    "mandou muito bem": "Ou fè trè byen",

    # Cordialidade
    "obrigado": "Mèsi",
    "obrigada": "Mèsi",
    "muito obrigado": "Mèsi anpil",
    "muito obrigada": "Mèsi anpil",
    "obrigado mesmo": "Mèsi anpil",
    "valeu mesmo": "Mèsi anpil",
    "de nada": "Pa gen pwoblèm",
    "imagina": "Pa gen pwoblèm",
    "por favor": "Tanpri",
    "se possível": "Si posib",
    "com licença": "Eskize m",
    "perdão": "Padon",
    "desculpa": "Eskize m",
    "desculpe": "Eskize m",
    "me desculpe": "Eskize m tanpri",
    "foi mal": "Eskize m",

    # Instrucao em workshop
    "presta atenção": "Koute byen",
    "presta atencao": "Koute byen",
    "preste atenção": "Koute byen",
    "olha aqui": "Gade isit la",
    "olha pra cá": "Gade isit la",
    "vê só": "Gade",
    "veja": "Gade",
    "entendeu?": "Ou konprann?",
    "entendeu": "Ou konprann?",
    "tá entendendo?": "Ou ap konprann?",
    "ta entendendo?": "Ou ap konprann?",
    "ficou claro?": "Sa klè?",
    "ficou claro": "Sa klè?",
    "alguma dúvida?": "Èske ou gen kesyon?",
    "alguma duvida?": "Èske ou gen kesyon?",
    "alguma pergunta?": "Èske ou gen kesyon?",
    "pode perguntar": "Ou ka mande",
    "tira a dúvida": "Mande kesyon w",
    "tira a duvida": "Mande kesyon w",

    # Comuns no dia a dia
    "vamos comer": "Annou manje",
    "tô com fome": "M grangou",
    "to com fome": "M grangou",
    "tô com sede": "M swaf",
    "to com sede": "M swaf",
    "quer água?": "Èske w vle dlo?",
    "quer agua?": "Èske w vle dlo?",
    "vamos descansar": "Annou repoze",
    "que horas são?": "Ki lè li ye?",
    "que horas sao?": "Ki lè li ye?",
}


# ============================================================
# 3. CALOR PÓS-NLLB (output kreyòl muito "técnico" -> versão acolhedora)
# ============================================================
# Quando o NLLB devolve uma tradução correta mas fria, substitui por uma versão
# culturalmente mais quente, usando gírias/expressões que aproximam o falante.

WARMTH_KR = [
    # ("regex caso-insensitivo no output do NLLB", "substituicao calorosa")
    (r"\bse trè fasil\b", "se dlo kòk"),         # "é muito fácil" -> "é água de coco" (gíria)
    (r"\btrè fasil\b", "dlo kòk"),               # "muito fácil" -> "água de coco"
    (r"\bfasil anpil\b", "dlo kòk"),             # "fácil demais" -> "água de coco"
    (r"\bsa bon\b", "sa bèl anpil"),             # "está bom" -> "está muito bonito"
    (r"\bli bon\b", "li bèl anpil"),             # "está bom" (3a pess) -> idem
    (r"\bmwen kontan\b", "kè m kontan"),         # "estou feliz" -> "meu coração está feliz" (mais quente)
]


def aplicar_calor(kr_text: str) -> str:
    """Pós-processa output do NLLB pra dar um toque cultural caloroso.
    Substitui frases técnicas por equivalentes mais acolhedores em kreyòl."""
    if not kr_text:
        return kr_text
    out = kr_text
    for pattern, warm in WARMTH_KR:
        out = re.sub(pattern, warm, out, flags=re.IGNORECASE)
    return out


# Pre-compute normalized lookups (key sem acentos -> valor)
_REWRITES_NORM = {_strip_accents(k): v for k, v in IDIOMA_REWRITES.items()}
_CULTURAL_NORM = {_strip_accents(k): v for k, v in IDIOMA_CULTURAL.items()}


def aplicar_reescrita(text: str) -> str:
    """Substitui idiomatismos PT por equivalentes literais antes de mandar pro NLLB.
    Ignora acentos no match (brasileiro nem sempre digita acento)."""
    if not text:
        return text
    # Trabalhar com versão normalizada pra detectar, mas devolver com novo texto literal
    norm_text = _strip_accents(text)
    result = norm_text
    # Maior chave primeiro pra evitar match de subexpressão (ex: "tá ligado?" antes de "tá")
    for norm_key in sorted(_REWRITES_NORM.keys(), key=len, reverse=True):
        if norm_key not in result:
            continue
        literal = _REWRITES_NORM[norm_key]
        pattern = r"\b" + re.escape(norm_key) + r"\b"
        result = re.sub(pattern, literal, result, flags=re.IGNORECASE)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def get_cultural_kr(text: str) -> Optional[str]:
    """Se a frase inteira for um idiomatismo conhecido, retorna o kreyòl cultural direto.
    Ignora acentos e pontuação final."""
    key = _strip_accents(text.strip()).rstrip(".!?,;")
    return _CULTURAL_NORM.get(key)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tests = [
        "Esse exercício é mamão com açúcar",
        "Dá um jeito aí",
        "Tá ligado o que eu falei?",
        "Ó, beleza, valeu cara",
        "Vou te ensinar rapidinho",
        "mamão com açúcar",
        "tudo bem?",
    ]
    print("=== REESCRITA (PT idiomatico -> PT literal) ===")
    for t in tests:
        print(f"  IN:  {t}")
        print(f"  OUT: {aplicar_reescrita(t)}\n")
    print("=== CULTURAL DIRETO (frase pura -> kreyòl) ===")
    for t in ["mamão com açúcar", "barbada", "valeu", "e aí?", "moleza"]:
        c = get_cultural_kr(t)
        print(f"  '{t}' -> {c if c else '(sem equivalente direto)'}")
