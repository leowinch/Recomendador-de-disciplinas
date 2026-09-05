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