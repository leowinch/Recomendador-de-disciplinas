from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import gerar_recomendacoes_agrupadas

class RecomendacaoView(APIView):
    """
    Recebe uma lista de códigos de disciplinas via POST,
    executa a clusterização e devolve os grupos formatados.
    """
    def post(self, request):
        # Captura os dados enviados no corpo do JSON pelo front-end
        codigos = request.data.get('codigos', [])
        topicos = request.data.get('topicos', [])
        
        if not isinstance(codigos, list):
            codigos = []
        if not isinstance(topicos, list):
            topicos = []

        if not codigos and not topicos:
            return Response(
                {"erro": "Envie ao menos uma disciplina cursada ou um tópico de interesse."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Chama a função de IA criada no services.py
            resultado = gerar_recomendacoes_agrupadas(codigos=codigos, topicos=topicos)
            
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