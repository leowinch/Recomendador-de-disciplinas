import numpy as np
from ast import literal_eval
from django.db import connection
from sklearn.cluster import AgglomerativeClustering
from .models import Disciplina

def gerar_recomendacoes_agrupadas(codigos: list[str], limite_busca: int = 30, max_por_cluster: int = 3):
    if not codigos:
        return []

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM buscar_por_historico(%s, %s);", [codigos, limite_busca])
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