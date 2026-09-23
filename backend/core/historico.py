import re
from pypdf import PdfReader

GRUPO_COMPLEMENTARES = 'Disciplinas Complementares de Graduação'

# Cabeçalhos de grupo como aparecem no histórico do Portal do Aluno (SIE/UFSM).
# A tabela de carga horária no fim do PDF repete alguns desses nomes, mas seguidos
# de números, então a comparação exata com a linha inteira não os confunde.
GRUPOS = (
    GRUPO_COMPLEMENTARES,
    'Formação Complementar e Humanística',
    'Núcleo de Formação Básica',
    'Núcleo de Formação Tecnológica',
    'Disciplinas de Outros Cursos',
)

# Ex.: "ELC1108      ANÁLISE E PROJETO DE SISTEMAS     60     4     Aprovado com nota     10,00"
LINHA_DISCIPLINA = re.compile(
    r'^\s*(?P<codigo>[A-Z]{2,}\d{2,})\s+(?P<nome>.+?)\s{2,}'
    r'(?P<ch>\d+)\s+(?P<cred>\d+)\s+(?P<situacao>\S.*?)(?:\s{2,}|$)'
)

SITUACOES_CONCLUIDAS = ('Aprovado', 'Dispensado', 'Aproveitamento')
SITUACOES_EM_ANDAMENTO = ('Matrícula',)


def _unicos(codigos):
    return list(dict.fromkeys(codigos))


def extrair_disciplinas(arquivo) -> list[dict]:
    """Lê o PDF do histórico e devolve uma entrada por linha de disciplina."""
    texto = '\n'.join(
        pagina.extract_text(extraction_mode='layout')
        for pagina in PdfReader(arquivo).pages
    )

    disciplinas = []
    grupo = None
    for linha in texto.splitlines():
        if linha.strip() in GRUPOS:
            grupo = linha.strip()
            continue

        m = LINHA_DISCIPLINA.match(linha)
        if m and grupo:
            disciplinas.append({
                'codigo': m['codigo'],
                'nome': m['nome'].strip(),
                'grupo': grupo,
                'situacao': m['situacao'].strip(),
            })
    return disciplinas


def resumir_historico(arquivo) -> dict:
    """
    Separa os códigos do histórico. Só 'complementares' (DCGs concluídas)
    alimenta o POST /api/recomendar/.
    """
    disciplinas = extrair_disciplinas(arquivo)
    concluidas = [d for d in disciplinas if d['situacao'].startswith(SITUACOES_CONCLUIDAS)]
    em_andamento = [d for d in disciplinas if d['situacao'].startswith(SITUACOES_EM_ANDAMENTO)]

    return {
        'complementares': _unicos(d['codigo'] for d in concluidas if d['grupo'] == GRUPO_COMPLEMENTARES),
        'cursadas': _unicos(d['codigo'] for d in concluidas),
        'em_andamento': _unicos(d['codigo'] for d in em_andamento),
        'disciplinas': disciplinas,
    }
