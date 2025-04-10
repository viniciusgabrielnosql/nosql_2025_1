class CollaborationPrediction(BaseModel):
    employee1: str
    employee2: str
    score: float

class CommunityDetectionResult(BaseModel):
    employee: str
    community_id: int

class CentralityResult(BaseModel):
    employee: str
    score: float

class PathResult(BaseModel):
    nodes: List[str]
    relationships: List[str]

class RankingResult(BaseModel):
    employee: str
    score: float

@app.get("/neo4j/link-prediction", response_model=List[CollaborationPrediction])
def predict_collaborations(limit: int = 5):
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (f1:Funcionario)-[:REQUER]->(d:DistribuicaoOS)<-[:REQUER]-(f2:Funcionario)
                WHERE f1.id < f2.id
                WITH f1, f2, count(d) AS score
                ORDER BY score DESC
                LIMIT $limit
                RETURN f1.nome AS employee1, f2.nome AS employee2, score
            """, {"limit": limit})
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/community-detection", response_model=List[CommunityDetectionResult])
def detect_communities():
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
                RETURN f.nome AS employee, communityId AS community_id
                ORDER BY community_id
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/centrality", response_model=List[CentralityResult])
def calculate_centrality():
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
                RETURN f.nome AS employee, score
                ORDER BY score DESC
                LIMIT 10
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/path/{specialty1}/{specialty2}", response_model=PathResult)
def find_path_between_specialties(specialty1: str, specialty2: str):
    try:
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (f1:Funcionario {especialidade: $specialty1}),
                      (f2:Funcionario {especialidade: $specialty2}),
                      p = shortestPath((f1)-[:REQUER*]-(f2))
                RETURN [n IN nodes(p) | n.nome] AS nodes, 
                       [r IN relationships(p) | type(r)] AS relationships
            """, {"specialty1": specialty1, "specialty2": specialty2})
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Path not found")
            
            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neo4j/ranking", response_model=List[RankingResult])
def rank_employees():
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
                RETURN f.nome AS employee, score
                ORDER BY score DESC
                LIMIT 10
            """)
            return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
