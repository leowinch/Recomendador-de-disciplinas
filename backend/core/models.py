# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Aluno(models.Model):
    pk = models.CompositePrimaryKey('id_curso', 'cod_aluno')
    id_curso = models.ForeignKey('Curso', models.DO_NOTHING, db_column='id_curso')
    cod_aluno = models.TextField()

    class Meta:
        managed = False
        db_table = 'aluno'


class CargaHistorico(models.Model):
    cod_curso = models.IntegerField(db_column='COD_CURSO', blank=True, null=True)  # Field name made lowercase.
    nome_curso = models.TextField(db_column='NOME_CURSO', blank=True, null=True)  # Field name made lowercase.
    tipo_atividade = models.TextField(db_column='TIPO_ATIVIDADE', blank=True, null=True)  # Field name made lowercase.
    depto = models.TextField(db_column='DEPTO', blank=True, null=True)  # Field name made lowercase.
    ch_minima = models.DecimalField(db_column='CH_MINIMA', blank=True, null=True)  # Field name made lowercase.
    num_versao = models.IntegerField(db_column='NUM_VERSAO', blank=True, null=True)  # Field name made lowercase.
    cod_ativ_curric = models.TextField(db_column='COD_ATIV_CURRIC', blank=True, null=True)  # Field name made lowercase.
    nome_ativ_curric = models.TextField(db_column='NOME_ATIV_CURRIC', blank=True, null=True)  # Field name made lowercase.
    ch_total = models.DecimalField(db_column='CH_TOTAL', blank=True, null=True)  # Field name made lowercase.
    creditos = models.DecimalField(db_column='CREDITOS', blank=True, null=True)  # Field name made lowercase.
    ano = models.IntegerField(db_column='ANO', blank=True, null=True)  # Field name made lowercase.
    periodo = models.TextField(db_column='PERIODO', blank=True, null=True)  # Field name made lowercase.
    media_final = models.DecimalField(db_column='MEDIA_FINAL', blank=True, null=True)  # Field name made lowercase.
    situacao = models.TextField(db_column='SITUACAO', blank=True, null=True)  # Field name made lowercase.
    cod_aluno = models.TextField(db_column='COD_ALUNO', blank=True, null=True)  # Field name made lowercase.
    forma_evasao = models.TextField(db_column='FORMA_EVASAO', blank=True, null=True)  # Field name made lowercase.
    semestre_aluno = models.TextField(db_column='SEMESTRE_ALUNO', blank=True, null=True)  # Field name made lowercase.
    semestre_rel_aluno = models.IntegerField(db_column='SEMESTRE_REL_ALUNO', blank=True, null=True)  # Field name made lowercase.
    semestre_rel_ativ = models.IntegerField(db_column='SEMESTRE_REL_ATIV', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'carga_historico'


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True)
    nome = models.TextField(unique=True)
    departamento = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'curso'


class Disciplina(models.Model):
    codigo = models.TextField(primary_key=True)
    nome = models.TextField(blank=True, null=True)
    periodo = models.IntegerField(blank=True, null=True)
    carga_horaria = models.IntegerField(blank=True, null=True)
    ementa = models.TextField(blank=True, null=True)
    objetivo = models.TextField(blank=True, null=True)
    bibliografia = models.TextField(blank=True, null=True)
    programa = models.TextField(blank=True, null=True)
    situacao = models.TextField(blank=True, null=True)
    embedding = models.TextField(blank=True, null=True)  # This field type is a guess.
    cluster_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'disciplina'


class DisciplinaCurso(models.Model):
    pk = models.CompositePrimaryKey('codigo', 'id_curso')
    codigo = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='codigo')
    id_curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='id_curso')

    class Meta:
        managed = False
        db_table = 'disciplina_curso'


class DisciplinaHorario(models.Model):
    pk = models.CompositePrimaryKey('codigo', 'id_horario', 'turma')
    codigo = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='codigo')
    id_horario = models.ForeignKey('Horario', models.DO_NOTHING, db_column='id_horario')
    turma = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'disciplina_horario'


class Historico(models.Model):
    id_historico = models.AutoField(primary_key=True)
    id_curso = models.IntegerField(blank=True, null=True)
    cod_aluno = models.TextField()
    cod_disciplina = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='cod_disciplina', blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    periodo = models.TextField(blank=True, null=True)
    situacao = models.TextField(blank=True, null=True)
    media_final = models.DecimalField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'historico'


class Horario(models.Model):
    id_horario = models.AutoField(primary_key=True)
    dia = models.TextField(blank=True, null=True)
    inicio = models.TimeField(blank=True, null=True)
    fim = models.TimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'horario'


class PreRequisitoDisciplina(models.Model):
    pk = models.CompositePrimaryKey('codigo_disciplina', 'codigo_prerequisito')
    codigo_disciplina = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='codigo_disciplina')
    codigo_prerequisito = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='codigo_prerequisito', related_name='prerequisitodisciplina_codigo_prerequisito_set')

    class Meta:
        managed = False
        db_table = 'pre_requisito_disciplina'


class PreRequisitoPeriodo(models.Model):
    pk = models.CompositePrimaryKey('codigo_disciplina', 'periodo_minimo')
    codigo_disciplina = models.ForeignKey(Disciplina, models.DO_NOTHING, db_column='codigo_disciplina')
    periodo_minimo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'pre_requisito_periodo'
