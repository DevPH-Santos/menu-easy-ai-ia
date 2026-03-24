import mysql.connector
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# carrega o .env
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)

cursor = conn.cursor()

# pegar usuarios
cursor.execute("SELECT pk_cpf_usuario FROM Usuario")
usuarios = [row[0] for row in cursor.fetchall()]

# pegar produtos
cursor.execute("SELECT pk_id_prod FROM Produtos")
produtos = [row[0] for row in cursor.fetchall()]

pedidos_ids = []

# ---------------------
# GERAR PEDIDOS
# ---------------------

for i in range(12000):

    cpf = random.choice(usuarios)

    data = datetime.now() - timedelta(days=random.randint(0,180))
    hora = (datetime.min + timedelta(
        hours=random.randint(8,22),
        minutes=random.randint(0,59),
        seconds=random.randint(0,59)
    )).time()

    clima = random.choice(["ensolarado", "frio", "nublado", "chuvoso"])  # ✅ corrigido

    promocao = random.choice([0,1])
    pessoas = random.randint(1,5)

    cursor.execute("""
    INSERT INTO Pedidos
    (ped_hr, ped_data, ped_clima, ped_tem_promocao, ped_qtd_pessoas_mesa, fk_cpf_usuario)
    VALUES (%s, %s, %s, %s, %s, %s)
    """,
    (hora, data, clima, promocao, pessoas, cpf))  # ✅ corrigido

    ped_id = cursor.lastrowid
    pedidos_ids.append(ped_id)

conn.commit()

print("Pedidos criados")

# ---------------------
# GERAR ITENS
# ---------------------

for ped in pedidos_ids:

    qtd_itens = random.randint(1,3)
    escolhidos = random.sample(produtos, qtd_itens)

    for prod in escolhidos:

        quant = random.randint(1,2)

        cursor.execute("""
        SELECT preco_prod FROM Produtos WHERE pk_id_prod=%s
        """, (prod,))

        preco = cursor.fetchone()[0]

        cursor.execute("""
        INSERT INTO Itens_Pedido
        (quant_prod, preco_unitario, fk_id_ped, fk_id_prod)
        VALUES (%s, %s, %s, %s)
        """,
        (quant, preco, ped, prod))

conn.commit()

print("Itens criados")

conn.close()