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
SITUACOES_REPROVADAS = ('Reprovado',)

# Cabeçalho, repetido em toda página. Ex.:
# "Curso: 314 - SISTEMAS DE INFORMAÇÃO                         Versão: 2009"
# "Forma de Ingresso: Processo Seletivo - SiSu / MEC           Período: 2. Semestre de 2024"
LINHA_CURSO = re.compile(r'^\s*Curso:\s*(?P<codigo>\d+)\s*-\s*(?P<nome>.+?)(?:\s{2,}|$)', re.MULTILINE)
PERIODO_INGRESSO = re.compile(r'Per[ií]odo:\s*(?P<semestre>[12])\.\s*Semestre de\s+(?P<ano>\d{4})')


def _unicos(codigos):
    return list(dict.fromkeys(codigos))


def ler_texto(arquivo) -> str:
    return '\n'.join(
        pagina.extract_text(extraction_mode='layout')
        for pagina in PdfReader(arquivo).pages
    )


def extrair_cabecalho(texto: str) -> dict:
    """Curso e período de ingresso do aluno; None no que não for encontrado."""
    curso = LINHA_CURSO.search(texto)
    ingresso = PERIODO_INGRESSO.search(texto)
    return {
        'curso': {'codigo': curso['codigo'], 'nome': curso['nome'].strip()} if curso else None,
        'ingresso': {'ano': int(ingresso['ano']), 'semestre': int(ingresso['semestre'])} if ingresso else None,
    }


def extrair_disciplinas(texto: str) -> list[dict]:
    """Devolve uma entrada por linha de disciplina do texto do histórico."""
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
    alimenta o POST /api/recomendar/. 'curso', 'ingresso' e 'disciplinas' voltam
    no POST /api/obrigatorias-pendentes/.
    """
    texto = ler_texto(arquivo)
    disciplinas = extrair_disciplinas(texto)
    concluidas = [d for d in disciplinas if d['situacao'].startswith(SITUACOES_CONCLUIDAS)]
    em_andamento = [d for d in disciplinas if d['situacao'].startswith(SITUACOES_EM_ANDAMENTO)]

    return {
        'complementares': _unicos(d['codigo'] for d in concluidas if d['grupo'] == GRUPO_COMPLEMENTARES),
        'cursadas': _unicos(d['codigo'] for d in concluidas),
        'em_andamento': _unicos(d['codigo'] for d in em_andamento),
        'disciplinas': disciplinas,
        **extrair_cabecalho(texto),
    }
