import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()  # carrega o .env

def conectar():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )
    return conn

def salvar_recomendacoes(conn, usuario_id, produtos):
    cursor = conn.cursor()
    for produto in produtos:
        cursor.execute("""
            INSERT INTO Recomendacao_Log (rec_aceita, fk_cpf_usuario, fk_id_prod)
            VALUES (0, %s, %s)
        """, (usuario_id, int(produto)))
    conn.commit()

def atualizar_feedback(conn, usuario_id, produtos_pedidos):
    """
    Atualiza rec_aceita = 1 para os produtos que o usuário realmente pediu.
    Busca as recomendações do último dia ainda não avaliadas.
    """
    cursor = conn.cursor()
    for produto in produtos_pedidos:
        cursor.execute("""
            UPDATE Recomendacao_Log
            SET rec_aceita = 1
            WHERE fk_cpf_usuario = %s
              AND fk_id_prod = %s
              AND rec_aceita = 0
              AND rec_data >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            LIMIT 1
        """, (usuario_id, int(produto)))
    conn.commit()
    return cursor.rowcount

def buscar_usuario(conn, cpf):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT idade_usuario
        FROM Usuario
        WHERE pk_cpf_usuario = %s
    """, (cpf,))
    row = cursor.fetchone()
    if row:
        return {"idade_usuario": row[0]}
    return None