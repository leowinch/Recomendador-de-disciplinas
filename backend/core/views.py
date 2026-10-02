from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from pypdf.errors import PdfReadError
from .services import gerar_recomendacoes_agrupadas
from .historico import resumir_historico
from .catalogo import buscar_disciplinas, detalhar_disciplina
from .obrigatorias import recomendar_obrigatorias

TAMANHO_MAX_HISTORICO = 5 * 1024 * 1024  # 5 MB

class RecomendacaoView(APIView):
    """
    Recebe uma lista de códigos de disciplinas via POST,
    executa a clusterização e devolve os grupos formatados.
    """
    def post(self, request):
        # Captura os dados enviados no corpo do JSON pelo front-end
        codigos = request.data.get('codigos', [])
        
        # Validação simples
        if not codigos or not isinstance(codigos, list):
            return Response(
                {"erro": "Envie uma lista de códigos no campo 'codigos'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Chama a função de IA criada no services.py
            resultado = gerar_recomendacoes_agrupadas(codigos=codigos)
            
            return Response({
                "sucesso": True,
                "total_clusters": len(resultado),
                "clusters": resultado
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"erro": f"Erro interno no servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HistoricoView(APIView):
    """
    Recebe o PDF do histórico escolar (campo 'arquivo', multipart) e devolve
    os códigos extraídos. O arquivo é lido em memória e não é salvo.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        arquivo = request.FILES.get('arquivo')

        if not arquivo:
            return Response(
                {"erro": "Envie o PDF do histórico no campo 'arquivo'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if arquivo.size > TAMANHO_MAX_HISTORICO:
            return Response(
                {"erro": "Arquivo maior que 5 MB."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if arquivo.read(5) != b'%PDF-':
            return Response(
                {"erro": "O arquivo enviado não é um PDF."},
                status=status.HTTP_400_BAD_REQUEST
            )
        arquivo.seek(0)

        try:
            resultado = resumir_historico(arquivo)
        except PdfReadError:
            return Response(
                {"erro": "Não foi possível ler o PDF."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not resultado['disciplinas']:
            return Response(
                {"erro": "Nenhuma disciplina encontrada. O PDF é o histórico do Portal do Aluno UFSM?"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response({"sucesso": True, **resultado}, status=status.HTTP_200_OK)


class ObrigatoriasPendentesView(APIView):
    """
    Recebe 'curso', 'ingresso' e 'disciplinas' como devolvidos pelo
    /api/importar-historico/ e devolve as obrigatórias atrasadas e as do
    semestre em que o aluno está.
    """
    def post(self, request):
        curso = request.data.get('curso')
        ingresso = request.data.get('ingresso')
        disciplinas = request.data.get('disciplinas', [])

        if not curso or not isinstance(curso, str):
            return Response(
                {"erro": "Envie o nome do curso no campo 'curso'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if (
            not isinstance(ingresso, dict)
            or type(ingresso.get('ano')) is not int
            or ingresso.get('semestre') not in (1, 2)
        ):
            return Response(
                {"erro": "Envie o período de ingresso no campo 'ingresso' ({ano, semestre})."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(disciplinas, list) or not all(isinstance(d, dict) for d in disciplinas):
            return Response(
                {"erro": "Envie as disciplinas do histórico no campo 'disciplinas'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        resultado = recomendar_obrigatorias(curso, ingresso, disciplinas, timezone.localdate())
        if resultado is None:
            return Response(
                {"erro": f"Currículo do curso {curso} não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({"sucesso": True, **resultado}, status=status.HTTP_200_OK)


class BuscaDisciplinaView(APIView):
    """GET ?q=termo — busca disciplinas por código ou nome, já com as turmas e horários."""
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response(
                {"erro": "Digite ao menos 2 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"disciplinas": buscar_disciplinas(q)}, status=status.HTTP_200_OK)


class DetalheDisciplinaView(APIView):
    """Dados de uma disciplina para o modal: turmas/horários, ementa, objetivo e cursos."""
    def get(self, request, codigo):
        disciplina = detalhar_disciplina(codigo)
        if not disciplina:
            return Response(
                {"erro": f"Disciplina {codigo} não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(disciplina, status=status.HTTP_200_OK)
