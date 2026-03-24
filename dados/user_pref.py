import random
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

# carrega variáveis do .env
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)

cursor = conn.cursor()

# -----------------------------
# CONFIG
# -----------------------------

senha_padrao = "123456"
senha_hash = bcrypt.hashpw(senha_padrao.encode(), bcrypt.gensalt()).decode()

# -----------------------------
# GERAR 800 USUÁRIOS
# -----------------------------

usuarios = []

for i in range(800):
    cpf = str(10000000000 + i)
    idade = random.randint(18, 60)

    usuarios.append((cpf, senha_hash, idade))  # 🔥 senha já criptografada

# 🔥 INSERÇÃO EM LOTE
cursor.executemany("""
    INSERT INTO Usuario (pk_cpf_usuario, senha_usuario, idade_usuario)
    VALUES (%s, %s, %s)
""", usuarios)

conn.commit()

print("✅ Usuarios inseridos (senha padrão: 123456)")

# -----------------------------
# GERAR PREFERÊNCIAS
# -----------------------------

cursor.execute("SELECT pk_id_caracteristica FROM Caracteristica")
caracteristicas = [row[0] for row in cursor.fetchall()]

preferencias = []

for cpf, _, _ in usuarios:
    
    gostos = random.sample(caracteristicas, random.randint(3, 6))
    
    for c in gostos:
        preferencias.append((cpf, c))

# 🔥 INSERÇÃO EM LOTE
cursor.executemany("""
    INSERT INTO Preferencia_Usuario (fk_cpf_usuario, fk_id_caracteristica)
    VALUES (%s, %s)
""", preferencias)

conn.commit()

print("✅ Preferencias inseridas")

conn.close()