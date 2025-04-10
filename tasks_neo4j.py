class previs_colab(BaseModel):
    func1: str
    func2: str
    pontos: float

class comunidade_detec(BaseModel):
    func: str
    comunidade_id: int

class calc_centralidade(BaseModel):
    func: str
    pontos: float

class path_especialidade(BaseModel):
    nodes: List[str]
    relacao: List[str]

class ranking_func(BaseModel):
    func: str
    pontos: float

@app.get("/neo4j/link-prediction", response_model=List[previs_colab])
def previs_colaboracao(limit: int = 5):
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (f1:Funcionario)-[:REQUER]->(d:DistribuicaoOS)<-[:REQUER]-(f2:Funcionario)
                WHERE f1.id < f2.id
                WITH f1, f2, count(d) AS score
                ORDER BY score DESC
                LIMIT $limit
                RETURN f1.nome AS func1, f2.nome AS func2, pontos
            """, {"limit": limit})
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/community-detection", response_model=List[comunidade_detec])
def detectar_comunidade():
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                CALL gds.louvain.stream({
                    nodeQuery: 'MATCH (f:Funcionario) RETURN id(f) AS id',
                    relationshipQuery: '''
                        MATCH (f1:Funcionario)-[:REQUER]->(d:DistribuicaoOS)<-[:REQUER]-(f2:Funcionario)
                        RETURN id(f1) AS source, id(f2) AS target, count(d) AS weight
                    '''
                })
                YIELD nodeId, communityId
                MATCH (f:Funcionario) WHERE id(f) = nodeId
                RETURN f.nome AS func, communityId AS comunidade_id
                ORDER BY comunidade_id
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/centrality", response_model=List[calc_centralidade])
def calcular_centralidade():
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                CALL gds.betweenness.stream({
                    nodeQuery: 'MATCH (f:Funcionario) RETURN id(f) AS id',
                    relationshipQuery: '''
                        MATCH (f1:Funcionario)-[:REQUER]->(d:DistribuicaoOS)<-[:REQUER]-(f2:Funcionario)
                        RETURN id(f1) AS source, id(f2) AS target
                    '''
                })
                YIELD nodeId, score
                MATCH (f:Funcionario) WHERE id(f) = nodeId
                RETURN f.nome AS func, pontos
                ORDER BY score DESC
                LIMIT 10
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/path/{specialty1}/{specialty2}", response_model=path_especialidade)
def path_especialidade(specialty1: str, specialty2: str):
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (f1:Funcionario {especialidade: $specialty1}),
                      (f2:Funcionario {especialidade: $specialty2}),
                      p = shortestPath((f1)-[:REQUER*]-(f2))
                RETURN [n IN nodes(p) | n.nome] AS nodes, 
                       [r IN relacao(p) | type(r)] AS relacao
            """, {"specialty1": specialty1, "specialty2": specialty2})
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Path not found")
            
            return {
                "nodes": record["nodes"],
                "relacao": record["relacao"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/ranking", response_model=List[ranking_func])
def rank_func():
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                CALL gds.pageRank.stream({
                    nodeQuery: 'MATCH (f:Funcionario) RETURN id(f) AS id',
                    relationshipQuery: '''
                        MATCH (f1:Funcionario)-[:REQUER]->(d:DistribuicaoOS)<-[:REQUER]-(f2:Funcionario)
                        RETURN id(f1) AS source, id(f2) AS target, count(d) AS weight
                    '''
                })
                YIELD nodeId, score
                MATCH (f:Funcionario) WHERE id(f) = nodeId
                RETURN f.nome AS func, pontos
                ORDER BY score DESC
                LIMIT 10
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
