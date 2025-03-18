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

# 🔍 Criando índices para otimizar consultas
funcionarios.create_index("especialidade_func")
clientes.create_index("servico_contratado")
ordens_servico.create_index("id_cliente")
distribuicoes_os.create_index([("especialidade_func", 1), ("habilitacao", 1)])

# 🚀 Inicialização do FastAPI
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

# 🔎 Busca Ordens de Serviço por ID do Cliente (usando índice)
@app.get("/ordens_servico/cliente/{id_cliente}")
def buscar_ordens_por_cliente(id_cliente: str):
    servicos = list(ordens_servico.find({"id_cliente": id_cliente}, {"_id": 0}))
    if not servicos:
        raise HTTPException(status_code=404, detail="Nenhuma ordem de serviço encontrada para esse cliente.")
    return {"ordens_servico": servicos}

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

# 🔎 Busca funcionários qualificados por especialidade e habilitação (usando índice composto)
@app.get("/funcionarios/qualificados/")
def buscar_funcionarios_qualificados(especialidade: str, habilitacao: str):
    query = {"especialidade_func": especialidade, "habilitacao": habilitacao}

    funcionarios_encontrados = list(funcionarios.find(query, {"_id": 0}))  

    if not funcionarios_encontrados:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum funcionário encontrado com especialidade '{especialidade}' e habilitação '{habilitacao}'."
        )

    return {"funcionarios_qualificados": funcionarios_encontrados}

# 🏠 Rota de teste
@app.get("/")
def root():
    return {"mensagem": "API de gerenciamento de ordens de serviço funcionando com índices otimizados!"}
