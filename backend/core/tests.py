from datetime import date
from django.test import SimpleTestCase
from .historico import extrair_cabecalho
from .obrigatorias import _mesmo_nome, _normalizar, semestre_do_aluno


class SemestreDoAlunoTests(SimpleTestCase):
    def test_conta_o_semestre_de_ingresso_e_o_atual(self):
        ingresso = {'ano': 2024, 'semestre': 2}
        self.assertEqual(semestre_do_aluno(ingresso, date(2024, 9, 1)), 1)
        self.assertEqual(semestre_do_aluno(ingresso, date(2025, 3, 1)), 2)
        self.assertEqual(semestre_do_aluno(ingresso, date(2026, 10, 2)), 5)

    def test_ingresso_no_primeiro_semestre(self):
        ingresso = {'ano': 2023, 'semestre': 1}
        self.assertEqual(semestre_do_aluno(ingresso, date(2023, 6, 30)), 1)
        self.assertEqual(semestre_do_aluno(ingresso, date(2023, 7, 1)), 2)
        self.assertEqual(semestre_do_aluno(ingresso, date(2026, 1, 15)), 7)

    def test_ingresso_futuro_fica_no_primeiro(self):
        self.assertEqual(semestre_do_aluno({'ano': 2027, 'semestre': 1}, date(2026, 10, 2)), 1)


class MesmoNomeTests(SimpleTestCase):
    def mesmo(self, a, b):
        return _mesmo_nome(_normalizar(a), _normalizar(b))

    def test_ignora_acento_caixa_e_aspas(self):
        self.assertTrue(self.mesmo('CIRCUÍTOS DIGITAIS', 'Circuitos Digitais'))
        self.assertTrue(self.mesmo('CÁLCULO "A"', 'CÁLCULO A'))

    def test_letra_de_variante_so_de_um_lado(self):
        self.assertTrue(self.mesmo('ENGENHARIA DE SOFTWARE "A"', 'ENGENHARIA DE SOFTWARE'))
        self.assertTrue(self.mesmo('MATEMÁTICA DISCRETA', 'MATEMÁTICA DISCRETA "A"'))

    def test_variantes_diferentes_nao_casam(self):
        self.assertFalse(self.mesmo('CÁLCULO "A"', 'CÁLCULO "B"'))

    def test_numeral_romano_nao_e_variante(self):
        self.assertFalse(self.mesmo('LABORATÓRIO DE PROGRAMAÇÃO I', 'LABORATÓRIO DE PROGRAMAÇÃO'))
        self.assertFalse(self.mesmo('LABORATÓRIO DE PROGRAMAÇÃO I', 'LABORATÓRIO DE PROGRAMAÇÃO II'))


class CabecalhoTests(SimpleTestCase):
    def test_extrai_curso_e_ingresso(self):
        texto = (
            'Curso: 314 - SISTEMAS DE INFORMAÇÃO                              Versão: 2009\n'
            'Nome: FULANO DE TAL\n'
            'Forma de Ingresso: Processo Seletivo - SiSu / MEC          Período: 2. Semestre de 2023\n'
        )
        self.assertEqual(extrair_cabecalho(texto), {
            'curso': {'codigo': '314', 'nome': 'SISTEMAS DE INFORMAÇÃO'},
            'ingresso': {'ano': 2023, 'semestre': 2},
        })

    def test_cabecalho_ausente(self):
        self.assertEqual(extrair_cabecalho('qualquer coisa'), {'curso': None, 'ingresso': None})
