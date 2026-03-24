import random
from datetime import datetime, timedelta
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="rs",
    port=3306
)

cursor = conn.cursor()

# pegar usuarios
cursor.execute("SELECT pk_cpf_usuario FROM Usuario")
usuarios = [row[0] for row in cursor.fetchall()]

# pegar produtos
cursor.execute("SELECT pk_id_prod FROM Produtos")
produtos = [row[0] for row in cursor.fetchall()]

avaliacoes = set()
max_tentativas = 10000

while len(avaliacoes) < 5000 and max_tentativas > 0:
    
    max_tentativas -= 1

    usuario = random.choice(usuarios)
    produto = random.choice(produtos)
    
    if (usuario, produto) in avaliacoes:
        continue
    
    avaliacoes.add((usuario, produto))

    nota = random.randint(1, 3)

    data = datetime.now() - timedelta(
        days=random.randint(0, 180),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    
    cursor.execute("""
    INSERT INTO Avaliacao
    (nota, aval_data, fk_cpf_usuario, fk_id_prod)
    VALUES (%s, %s, %s, %s)
    """, (nota, data, usuario, produto))

conn.commit()

print("5000 avaliações criadas")

conn.close()