import unicodedata
from django.db.models import Case, Exists, F, Func, IntegerField, OuterRef, Q, TextField, Value, When
from .models import Disciplina, DisciplinaCurso, DisciplinaHorario

# O banco guarda o dia por extenso ("Segunda-feira"); o front trabalha com a sigla.
DIAS = {
    'Segunda-feira': 'Seg',
    'Terça-feira': 'Ter',
    'Quarta-feira': 'Qua',
    'Quinta-feira': 'Qui',
    'Sexta-feira': 'Sex',
    'Sábado': 'Sáb',
}
ORDEM_DIAS = list(DIAS.values())

# periodo = 99 é usado para disciplinas sem semestre fixo no currículo
PERIODO_SEM_SEMESTRE = 99


def _sem_acento(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def turmas_por_codigo(codigos) -> dict[str, list[dict]]:
    """{codigo: [{turma, horarios: [{dia, inicio, fim}]}]}, com turmas e horários ordenados."""
    linhas = DisciplinaHorario.objects.filter(codigo__in=codigos).values(
        'codigo', 'turma',
        dia=F('id_horario__dia'), inicio=F('id_horario__inicio'), fim=F('id_horario__fim'),
    )

    agrupado = {}
    for l in linhas:
        dia = DIAS.get(l['dia'])
        if not dia or not l['inicio'] or not l['fim']:
            continue
        horarios = agrupado.setdefault(l['codigo'], {}).setdefault(l['turma'], [])
        horarios.append({
            'dia': dia,
            'inicio': l['inicio'].strftime('%H:%M'),
            'fim': l['fim'].strftime('%H:%M'),
        })

    resultado = {}
    for codigo, turmas in agrupado.items():
        resultado[codigo] = [
            {
                'turma': turma,
                'horarios': sorted(horarios, key=lambda h: (ORDEM_DIAS.index(h['dia']), h['inicio'])),
            }
            for turma, horarios in sorted(turmas.items())
        ]
    return resultado


def buscar_disciplinas(q: str, limite: int = 20) -> list[dict]:
    """
    Busca por código ou nome, ignorando acentos e caixa. Código exato vem primeiro,
    depois código que começa com o termo, e dentro disso as que têm turma ofertada.
    """
    # Nomes como 'CÁLCULO "A"' têm aspas; tirar dos dois lados faz 'calculo a' casar.
    termo = _sem_acento(q.replace('"', '').strip())

    qs = (
        Disciplina.objects
        .annotate(nome_sem_acento=Func(
            Func(F('nome'), Value('"'), Value(''), function='replace', output_field=TextField()),
            function='unaccent',
            output_field=TextField(),
        ))
        .filter(Q(codigo__istartswith=termo) | Q(nome_sem_acento__icontains=termo))
        .annotate(
            prioridade=Case(
                When(codigo__iexact=termo, then=Value(0)),
                When(codigo__istartswith=termo, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            tem_turma=Exists(DisciplinaHorario.objects.filter(codigo=OuterRef('codigo'))),
        )
        .order_by('prioridade', '-tem_turma', 'nome')
        .values('codigo', 'nome', 'carga_horaria')[:limite]
    )

    disciplinas = list(qs)
    turmas = turmas_por_codigo([d['codigo'] for d in disciplinas])
    for d in disciplinas:
        d['turmas'] = turmas.get(d['codigo'], [])
    return disciplinas


def detalhar_disciplina(codigo: str) -> dict | None:
    d = (
        Disciplina.objects.filter(codigo=codigo)
        .values('codigo', 'nome', 'carga_horaria', 'periodo', 'situacao', 'ementa', 'objetivo')
        .first()
    )
    if not d:
        return None

    if d['periodo'] == PERIODO_SEM_SEMESTRE:
        d['periodo'] = None
    d['cursos'] = list(
        DisciplinaCurso.objects.filter(codigo=codigo)
        .order_by('id_curso__nome')
        .values_list('id_curso__nome', flat=True)
    )
    d['turmas'] = turmas_por_codigo([codigo]).get(codigo, [])
    return d
