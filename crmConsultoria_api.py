from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pydantic import BaseModel
from typing import List
import os
import redis

# Conexão com o MongoDB
password = os.getenv("MONGO_PASSWORD")
uri = f"mongodb+srv://viniciusgabrieldb2:{password}@cluster0.62hmy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Criar cliente e testar conexão
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["meu_banco"]

# Coleções do MongoDB
funcionarios = db["funcionarios"]
clientes = db["clientes"]
ordens_servico = db["ordens_servico"]
distribuicoes_os = db["distribuicoes_os"]

# 🔍 Criando índices para otimizar consultas
funcionarios.create_index("especialidade_func")
clientes.create_index("servico_contratado")
ordens_servico.create_index("id_cliente")
distribuicoes_os.create_index([("especialidade_func", 1), ("habilitacao", 1)])

# 🚀 Inicialização do FastAPI
app = FastAPI()

# Configuração do Redis
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# 🔢 Bitmap - Rastreamento binário

def registrar_acesso(chave: str, dia: int):
    """Marca o acesso de um usuário em um dia específico"""
    redis_client.setbit(chave, dia, 1)

def verificar_acesso(chave: str, dia: int) -> bool:
    """Verifica se o usuário acessou em um dia específico"""
    return redis_client.getbit(chave, dia) == 1

def contar_dias_ativos(chave: str) -> int:
    """Conta quantos dias o usuário esteve ativo"""
    return redis_client.bitcount(chave)

# 🌸 Bloom Filter - Testar se um item já foi visto
def adicionar_ao_bloom_filter(chave: str, valor: str):
    redis_client.execute_command("BF.ADD", chave, valor)

def verificar_bloom_filter(chave: str, valor: str) -> bool:
    return redis_client.execute_command("BF.EXISTS", chave, valor) == 1

# 📌 Modelos Pydantic para validação de entrada
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

# 📌 Rotas CRUD (POST para inserção e GET para listagem)

## 🏢 Funcionários
@app.post("/funcionarios/", response_model=Funcionario)
def criar_funcionario(funcionario: Funcionario):
    try:
        funcionarios.insert_one(funcionario.dict())
        return funcionario
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/funcionarios/")
def listar_funcionarios():
    return list(funcionarios.find({}, {"_id": 0}))

# 🔎 Busca funcionários por especialidade (usando índice)
@app.get("/funcionarios/especialidade/{especialidade}")
def buscar_funcionarios_por_especialidade(especialidade: str):
    return list(funcionarios.find({"especialidade_func": especialidade}, {"_id": 0}))

## 👤 Clientes
@app.post("/clientes/", response_model=Cliente)
def criar_cliente(cliente: Cliente):
    try:
        clientes.insert_one(cliente.dict())
        return cliente
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clientes/", response_model=List[Cliente])
def listar_clientes():
    return list(clientes.find({}, {"_id": 0}))

# 🔎 Busca clientes por serviço contratado (usando índice)
@app.get("/clientes/servico/{servico}")
def buscar_clientes_por_servico(servico: str):
    return list(clientes.find({"servico_contratado": servico}, {"_id": 0}))

## 📌 Redis - Bitmap e Bloom Filter
@app.post("/bitmap/registrar/{chave}/{dia}")
def registrar_bitmap(chave: str, dia: int):
    registrar_acesso(chave, dia)
    return {"mensagem": f"Acesso registrado para {chave} no dia {dia}"}

@app.get("/bitmap/verificar/{chave}/{dia}")
def verificar_bitmap(chave: str, dia: int):
    acessou = verificar_acesso(chave, dia)
    return {"acessou": acessou}

@app.get("/bitmap/contar/{chave}")
def contar_bitmap(chave: str):
    dias_ativos = contar_dias_ativos(chave)
    return {"dias_ativos": dias_ativos}

@app.post("/bloomfilter/adicionar/{chave}/{valor}")
def adicionar_bf(chave: str, valor: str):
    adicionar_ao_bloom_filter(chave, valor)
    return {"mensagem": "Valor adicionado ao Bloom Filter"}

@app.get("/bloomfilter/verificar/{chave}/{valor}")
def verificar_bf(chave: str, valor: str):
    existe = verificar_bloom_filter(chave, valor)
    return {"existe": existe}

# 🏠 Rota de teste
@app.get("/")
def root():
    return {"mensagem": "API de gerenciamento de ordens de serviço funcionando com índices otimizados!"}
