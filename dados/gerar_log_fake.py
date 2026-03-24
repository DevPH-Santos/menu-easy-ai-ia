import os
from dotenv import load_dotenv
import random
import mysql.connector
from datetime import datetime, timedelta


def gerar_logs_fake(conn, quantidade=5000):

    cursor = conn.cursor()

    # -----------------------------
    # PEGAR USUÁRIOS E PRODUTOS
    # -----------------------------
    cursor.execute("SELECT pk_cpf_usuario FROM Usuario")
    usuarios = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT pk_id_prod FROM Produtos")
    produtos = [row[0] for row in cursor.fetchall()]

    logs = []

    for _ in range(quantidade):

        usuario = random.choice(usuarios)
        produto = random.choice(produtos)

        # 🔥 ACEITAÇÃO BALANCEADA
        aceita = random.choice([0, 1])

        # leve tendência (opcional)
        if random.random() < 0.1:
            aceita = 1

        data = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        logs.append((data, aceita, usuario, produto))

    # -----------------------------
    # INSERÇÃO EM LOTE
    # -----------------------------
    cursor.executemany("""
        INSERT INTO Recomendacao_Log
        (rec_data, rec_aceita, fk_cpf_usuario, fk_id_prod)
        VALUES (%s, %s, %s, %s)
    """, logs)

    conn.commit()

    print(f"🔥 {quantidade} logs gerados com sucesso!")


# EXECUÇÃO DIRETA
if __name__ == "__main__":

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

    gerar_logs_fake(conn, quantidade=5000)

    conn.close()