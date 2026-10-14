import numpy as np
from ast import literal_eval
from django.db import connection
from sklearn.cluster import AgglomerativeClustering
from .models import Disciplina
from dotenv import load_dotenv
import os
import time
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

def gerar_embedding_texto(texto: str) -> list[float]:
    """
    Gera o vetor de 768 posições para o texto/tópicos informados.
    """

    while True:
        try:
            texto_para_embedding = f"Disciplina universitária, conteúdo acadêmico e ementa sobre: {texto}"
            resultado = client.models.embed_content(
                model="gemini-embedding-2",
                contents=texto_para_embedding,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY", output_dimensionality=768)
            )
            return resultado.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                print("Rate limit atingido, aguardando 60s...")
                time.sleep(60)
            else:
                print(f"Erro ao gerar embedding: {e}")
                return None


def gerar_recomendacoes_agrupadas(codigos: list[str], topicos: list[str] = None, limite_busca: int = 30, max_por_cluster: int = 3):
    if not codigos and not topicos:
        return []

    with connection.cursor() as cursor:
        if topicos:
            # Transforma a lista de tópicos em frase e gera o embedding
            texto_interesse = ", ".join(topicos)
            vetor_interesse = gerar_embedding_texto(texto_interesse)

            peso_interesse = 0.7  # ou deixa configurável depois

            cursor.execute(
                """
                SELECT * FROM buscar_por_interesse(%s::vector, %s::text[], %s, %s);
                """,
                [str(vetor_interesse), codigos, peso_interesse, limite_busca]
            )
        else:
            cursor.execute(
                "SELECT * FROM buscar_por_historico(%s, %s);",
                [codigos, limite_busca]
            )
        colunas = [col[0] for col in cursor.description]
        recomendacoes = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    if not recomendacoes:
        return []

    top_codigos = [r["codigo"] for r in recomendacoes]
    
    dados = list(
        Disciplina.objects.filter(codigo__in=top_codigos)
        .values("codigo", "nome", "embedding")
    )

    if not dados:
        return []
    
    if len(dados) == 1:
        dados[0]['grupo'] = 1
        return dados

    X = np.array([
        literal_eval(d["embedding"]) if isinstance(d["embedding"], str) else d["embedding"]
        for d in dados
    ])


    clusterizador = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.15,
        metric='cosine',
        linkage='average'
    )
    labels = clusterizador.fit_predict(X)


    clusters_map = {}
    for d, label in zip(dados, labels):
        label_int = int(label)
        if label_int not in clusters_map:
            clusters_map[label_int] = []
        
        clusters_map[label_int].append({
            "codigo": d["codigo"],
            "nome": d["nome"]
        })

    resultado = []
    for cluster_id in sorted(clusters_map.keys()):
        resultado.append({
            "cluster_id": cluster_id,
            "total_encontrados": len(clusters_map[cluster_id]),
            "disciplinas": clusters_map[cluster_id][:max_por_cluster]
        })

    return resultado