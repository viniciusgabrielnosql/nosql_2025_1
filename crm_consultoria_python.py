from pymongo import MongoClient


client = MongoClient("mongodb+srv://viniciusgabrieldb2:<db_password>@cluster0.62hmy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Selecionar o banco de dados
db = client["meu_banco"]

# Coleções
funcionarios = db["funcionarios"]
clientes = db["clientes"]
ordens_servico = db["ordens_servico"]
distribuicoes_os = db["distribuicoes_os"]

# Documentos
funcionario_doc = {
    "id_func": "001",
    "nome_func": "João José",
    "especialidade_func": "Outorga",
    "end_func": "Avenida João José",
    "data_contrato": "01/01/2025",
    "telefone_contato": "(34) 91111-2222",
    "email_contato": "joaojose@joao.com",
    "habilitacao": "Sim",
    "disponibilidade": "Disponível"
}

cliente_doc = {
    "id_cliente": "0000001",
    "nome_cliente": "José João",
    "end_cliente": "Fazenda Maria",
    "telefone_cliente": "(34) 91111-3333",
    "servico_contratado": "Outorga"
}

ordem_servico_doc = {
    "id_os": "xxxxxxx1",
    "id_cliente": "0000001",
    "data_solicitacao": "01/02/2025",
    "situacao": "Distribuindo"
}

distribuicao_os_doc = {
    "id_os": "xxxxxxx1",
    "id_cliente": "0000001",
    "data_distribuicao": "02/02/2025",
    "data_previsao": "05/02/2025",
    "especialidade_func": "Outorga",
    "qtd_func": 2,
    "habilitacao": "Sim"
}

# Inserir documentos no MongoDB
funcionarios.insert_one(funcionario_doc)
clientes.insert_one(cliente_doc)
ordens_servico.insert_one(ordem_servico_doc)
distribuicoes_os.insert_one(distribuicao_os_doc)
