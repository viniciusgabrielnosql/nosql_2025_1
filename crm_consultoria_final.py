from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pydantic import BaseModel
from typing import List
from neo4j import GraphDatabase
from fastapi.middleware.cors import CORSMiddleware
import os
import redis
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Conexão com o MongoDB
password = os.getenv("MONGO_PASSWORD")
uri = f"mongodb+srv://viniciusgabrieldb2:{password}@cluster0.62hmy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["meu_banco"]

funcionarios = db["funcionarios"]
clientes = db["clientes"]
ordens_servico = db["ordens_servico"]
distribuicoes_os = db["distribuicoes_os"]

funcionarios.create_index("especialidade_func")
clientes.create_index("servico_contratado")
ordens_servico.create_index("id_cliente")
distribuicoes_os.create_index([("especialidade_func", 1), ("habilitacao", 1)])

# Conexão com o Neo4j Aura
neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://64e579ad.databases.neo4j.io")
neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def testar_conexao_neo4j():
    try:
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 AS resultado")
            print("Conectado ao Neo4j com sucesso! Resultado:", result.single()["resultado"])
    except Exception as e:
        print("Erro ao conectar com Neo4j:", e)

testar_conexao_neo4j()

# Conexão com o Redis
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bitmap

def registrar_acesso(chave: str, dia: int):
    redis_client.setbit(chave, dia, 1)

def verificar_acesso(chave: str, dia: int) -> bool:
    return redis_client.getbit(chave, dia) == 1

def contar_dias_ativos(chave: str) -> int:
    return redis_client.bitcount(chave)

# Bloom Filter

def adicionar_ao_bloom_filter(chave: str, valor: str):
    redis_client.execute_command("BF.ADD", chave, valor)

def verificar_bloom_filter(chave: str, valor: str) -> bool:
    return redis_client.execute_command("BF.EXISTS", chave, valor) == 1

# Models Pydantic
class Funcionario(BaseModel):
    id_func: str
    nome_func: str
    especialidade_func: str
    end_func: str
    data_contrato: str
    telefone_contato: str
    email_contato: str
    habilitacao: str
    disponibilidade: str

class Cliente(BaseModel):
    id_cliente: str
    nome_cliente: str
    end_cliente: str
    telefone_cliente: str
    servico_contratado: str

class OrdemServico(BaseModel):
    id_os: str
    id_cliente: str
    data_solicitacao: str
    situacao: str

class DistribuicaoOS(BaseModel):
    id_os: str
    id_cliente: str
    data_distribuicao: str
    data_previsao: str
    especialidade_func: str
    qtd_func: int
    habilitacao: str

# Rotas MongoDB
@app.post("/funcionarios/", response_model=Funcionario)
def criar_funcionario(funcionario: Funcionario):
    funcionarios.insert_one(funcionario.dict())
    return funcionario

@app.get("/funcionarios/")
def listar_funcionarios():
    return list(funcionarios.find({}, {"_id": 0}))

@app.get("/funcionarios/especialidade/{especialidade}")
def buscar_funcionarios_por_especialidade(especialidade: str):
    return list(funcionarios.find({"especialidade_func": especialidade}, {"_id": 0}))

@app.post("/clientes/", response_model=Cliente)
def criar_cliente(cliente: Cliente):
    clientes.insert_one(cliente.dict())
    return cliente

@app.get("/clientes/", response_model=List[Cliente])
def listar_clientes():
    return list(clientes.find({}, {"_id": 0}))

@app.get("/clientes/servico/{servico}")
def buscar_clientes_por_servico(servico: str):
    return list(clientes.find({"servico_contratado": servico}, {"_id": 0}))

# Rotas Redis
@app.post("/bitmap/registrar/{chave}/{dia}")
def registrar_bitmap(chave: str, dia: int):
    registrar_acesso(chave, dia)
    return {"mensagem": f"Acesso registrado para {chave} no dia {dia}"}

@app.get("/bitmap/verificar/{chave}/{dia}")
def verificar_bitmap(chave: str, dia: int):
    return {"acessou": verificar_acesso(chave, dia)}

@app.get("/bitmap/contar/{chave}")
def contar_bitmap(chave: str):
    return {"dias_ativos": contar_dias_ativos(chave)}

@app.post("/bloomfilter/adicionar/{chave}/{valor}")
def adicionar_bf(chave: str, valor: str):
    adicionar_ao_bloom_filter(chave, valor)
    return {"mensagem": "Valor adicionado ao Bloom Filter"}

@app.get("/bloomfilter/verificar/{chave}/{valor}")
def verificar_bf(chave: str, valor: str):
    return {"existe": verificar_bloom_filter(chave, valor)}

# Rota de sincronização com Neo4j
@app.post("/sincronizar/neo4j")
def sincronizar_dados_para_neo4j():
    try:
        with neo4j_driver.session() as session:
            for c in clientes.find():
                session.run("""
                    MERGE (cliente:Cliente {id: $id})
                    SET cliente.nome = $nome, cliente.endereco = $endereco, cliente.telefone = $telefone
                """, id=c["id_cliente"], nome=c["nome_cliente"], endereco=c["end_cliente"], telefone=c["telefone_cliente"])

            for f in funcionarios.find():
                session.run("""
                    MERGE (func:Funcionario {id: $id})
                    SET func.nome = $nome, func.email = $email, func.telefone = $telefone,
                        func.especialidade = $especialidade, func.habilitacao = $habilitacao
                """, id=f["id_func"], nome=f["nome_func"], email=f["email_contato"], telefone=f["telefone_contato"],
                    especialidade=f["especialidade_func"], habilitacao=f["habilitacao"])

            for os_doc in ordens_servico.find():
                session.run("""
                    MERGE (os:OrdemServico {id: $id})
                    SET os.data = $data, os.situacao = $situacao
                    WITH os
                    MATCH (c:Cliente {id: $cliente_id})
                    MERGE (c)-[:SOLICITOU]->(os)
                """, id=os_doc["id_os"], data=os_doc["data_solicitacao"],
                    situacao=os_doc["situacao"], cliente_id=os_doc["id_cliente"])

            for dist in distribuicoes_os.find():
                dist_id = f"DIST_{dist['id_os']}"
                session.run("""
                    MERGE (d:DistribuicaoOS {id: $id})
                    SET d.data_distribuicao = $data_dist,
                        d.data_previsao = $data_prev,
                        d.qtd_func = $qtd,
                        d.especialidade = $especialidade,
                        d.habilitacao = $habilitacao
                    WITH d
                    MATCH (os:OrdemServico {id: $id_os})
                    MERGE (os)-[:FOI_DISTRIBUIDA_COM]->(d)
                """, id=dist_id, id_os=dist["id_os"],
                    data_dist=dist["data_distribuicao"], data_prev=dist["data_previsao"],
                    qtd=dist["qtd_func"], especialidade=dist["especialidade_func"], habilitacao=dist["habilitacao"])

                session.run("""
                    MATCH (d:DistribuicaoOS {id: $id})
                    MATCH (f:Funcionario)
                    WHERE f.especialidade = $especialidade AND f.habilitacao = $habilitacao
                    MERGE (d)-[:REQUER {especialidade: $especialidade, habilitacao: $habilitacao}]->(f)
                """, id=dist_id, especialidade=dist["especialidade_func"], habilitacao=dist["habilitacao"])

        return {"mensagem": "Dados sincronizados com sucesso no Neo4j"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"mensagem": "API com MongoDB, Redis e sincronização com Neo4j funcionando!"}
