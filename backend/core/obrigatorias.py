import re
from collections import Counter
from datetime import date
from django.db.models import F
from .catalogo import PERIODO_SEM_SEMESTRE, _sem_acento
from .historico import SITUACOES_CONCLUIDAS, SITUACOES_EM_ANDAMENTO, SITUACOES_REPROVADAS
from .models import Curso, DisciplinaCurso

# Letra de variante no fim do nome: 'CÁLCULO "A"', 'CUSTOS A'. Não pega I, V e X,
# que são numeração romana ("LABORATÓRIO DE PROGRAMAÇÃO I").
VARIANTE = re.compile(r' [A-H]$')


def _normalizar(texto: str) -> str:
    """Sem acento, caixa e pontuação: 'CIRCUÍTOS DIGITAIS' == 'Circuitos Digitais'."""
    return ' '.join(re.sub(r'[^A-Z0-9]+', ' ', _sem_acento(texto or '').upper()).split())


def _mesmo_nome(a: str, b: str) -> bool:
    """
    Nomes já normalizados. Iguais, ou iguais a menos da letra de variante quando só
    um dos dois a tem ('ENGENHARIA DE SOFTWARE A' e 'ENGENHARIA DE SOFTWARE').
    Com letra nos dois lados ela tem que bater: 'CALCULO A' não é 'CALCULO B'.
    """
    if a == b:
        return True
    base_a, base_b = VARIANTE.sub('', a), VARIANTE.sub('', b)
    return base_a == base_b and (base_a == a or base_b == b)


def semestre_letivo(hoje: date) -> tuple[int, int]:
    """(ano, semestre) em que a data cai: janeiro a junho é o 1º, julho a dezembro o 2º."""
    return hoje.year, 1 if hoje.month <= 6 else 2


def semestre_do_aluno(ingresso: dict, hoje: date) -> int:
    """Quantos semestres letivos, contando o de ingresso e o atual. Quem entrou em 2024/2 está no 5º em 2026/2."""
    ano, semestre = semestre_letivo(hoje)
    return max(1, (ano - ingresso['ano']) * 2 + (semestre - ingresso['semestre']) + 1)


def _obrigatorias():
    """Vínculos disciplina-curso cujo período é um semestre do currículo (nem 99 nem nulo)."""
    return (
        DisciplinaCurso.objects
        .filter(codigo__periodo__gte=1)
        .exclude(codigo__periodo=PERIODO_SEM_SEMESTRE)
    )


def encontrar_curso(nome: str) -> Curso | None:
    """
    O histórico traz "SISTEMAS DE INFORMAÇÃO" e o banco "Bacharelado Em Sistemas De
    Informação", então vale o nome do histórico contido no do banco. Só entram cursos
    com obrigatórias cadastradas; nome exato vem primeiro, depois o mais curto.
    """
    alvo = _normalizar(nome)
    if not alvo:
        return None

    candidatos = [
        c for c in Curso.objects.all()
        if f' {alvo} ' in f' {_normalizar(c.nome)} '
    ]
    com_obrigatorias = Counter(
        _obrigatorias()
        .filter(id_curso__in=[c.id_curso for c in candidatos])
        .values_list('id_curso', flat=True)
    )
    candidatos = [c for c in candidatos if com_obrigatorias[c.id_curso]]
    if not candidatos:
        return None
    return min(candidatos, key=lambda c: (_normalizar(c.nome) != alvo, len(c.nome), c.id_curso))


def recomendar_obrigatorias(nome_curso: str, ingresso: dict, disciplinas: list[dict], hoje: date) -> dict | None:
    """
    Obrigatórias do curso que o aluno ainda não concluiu nem está cursando, separadas
    em 'atrasadas' (de semestres anteriores ao dele) e 'do_semestre' (do semestre em
    que ele está). None se o curso não for encontrado.

    Uma obrigatória conta como feita se o código ou o nome aparece no histórico, porque
    currículos de versões diferentes usam códigos diferentes para a mesma disciplina.
    """
    curso = encontrar_curso(nome_curso)
    if not curso:
        return None

    def do_historico(situacoes):
        feitas = [d for d in disciplinas if str(d.get('situacao', '')).startswith(situacoes)]
        return {d.get('codigo') for d in feitas}, [_normalizar(d.get('nome')) for d in feitas]

    def consta(disciplina, codigos, nomes):
        nome = _normalizar(disciplina['nome'])
        return disciplina['codigo'] in codigos or any(_mesmo_nome(nome, n) for n in nomes)

    resolvidas = do_historico(SITUACOES_CONCLUIDAS + SITUACOES_EM_ANDAMENTO)
    reprovadas = do_historico(SITUACOES_REPROVADAS)

    curriculo = (
        _obrigatorias().filter(id_curso=curso)
        .order_by('codigo__periodo', 'codigo')
        .values('codigo', nome=F('codigo__nome'), periodo=F('codigo__periodo'),
                carga_horaria=F('codigo__carga_horaria'))
    )

    semestre = semestre_do_aluno(ingresso, hoje)
    atrasadas, do_semestre = [], []
    for d in curriculo:
        if d['periodo'] > semestre or consta(d, *resolvidas):
            continue
        d['motivo'] = 'reprovada' if consta(d, *reprovadas) else 'nao_cursada'
        (do_semestre if d['periodo'] == semestre else atrasadas).append(d)

    ano, semestre_ano = semestre_letivo(hoje)
    return {
        'curso': curso.nome,
        'semestre_aluno': semestre,
        'semestre_letivo': {'ano': ano, 'semestre': semestre_ano},
        'atrasadas': atrasadas,
        'do_semestre': do_semestre,
    }
