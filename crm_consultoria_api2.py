from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pydantic import BaseModel
from typing import List
import os

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

# Definição do app FastAPI
app = FastAPI()

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
    funcionarios_lista = list(funcionarios.find({}, {"_id": 0}))
    print("🔍 Dados retornados pela API:", funcionarios_lista)  # Adiciona um print para depuração
    return funcionarios_lista


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

## 📄 Ordens de Serviço
@app.post("/ordens_servico/", response_model=OrdemServico)
def criar_ordem_servico(ordem: OrdemServico):
    try:
        ordens_servico.insert_one(ordem.dict())
        return ordem
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ordens_servico/", response_model=List[OrdemServico])
def listar_ordens_servico():
    return list(ordens_servico.find({}, {"_id": 0}))

## 📌 Distribuições de OS
@app.post("/distribuicoes_os/", response_model=DistribuicaoOS)
def criar_distribuicao_os(distribuicao: DistribuicaoOS):
    try:
        distribuicoes_os.insert_one(distribuicao.dict())
        return distribuicao
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/distribuicoes_os/", response_model=List[DistribuicaoOS])
def listar_distribuicoes_os():
    return list(distribuicoes_os.find({}, {"_id": 0}))

# Rota de teste
@app.get("/")
def root():
    return {"mensagem": "API de gerenciamento de ordens de serviço funcionando!"}