from flask import Flask, request, jsonify
from flask_cors import CORS
from bd import conectar, salvar_recomendacoes, buscar_usuario, atualizar_feedback
from data import carregar_dados, calcular_contexto_score
from model import recomendar
from train_model import treinar_modelo
import importlib
import model

app = Flask(__name__)
CORS(app)  # ✅ libera CORS para o frontend em file://

def usuario_existe(conn, cpf):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Usuario WHERE pk_cpf_usuario = %s", (cpf,))
    return cursor.fetchone() is not None

def precisa_retreinar(conn, aceitos_novos=1):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM Recomendacao_Log
        WHERE rec_aceita = 1
    """)
    total = cursor.fetchone()[0]
    if total < 50:
        return False
    anterior = total - aceitos_novos
    return (total // 50) > (anterior // 50)

@app.route("/")
def home():
    return "API funcionando 🚀"

@app.route("/recomendar", methods=["POST"])
def recomendar_api():

    conn = conectar()
    dados = carregar_dados(conn)

    dados_front = request.json
    usuario = dados_front["cpf"]

    if not usuario_existe(conn, usuario):
        conn.close()
        return {"erro": "Usuário não cadastrado"}, 400

    dados_usuario = buscar_usuario(conn, usuario)

    if not dados_usuario:
        conn.close()
        return {"erro": "Usuário não encontrado"}, 400

    features_usuario = {
        "idade_usuario": dados_usuario["idade_usuario"],
        "hora": dados_front["hora"],
        "ped_qtd_pessoas_mesa": dados_front["pessoas"],
        "ped_tem_promocao": dados_front["promocao"],
        "ped_clima": dados_front["clima"].lower()
    }

    contexto_score = calcular_contexto_score(
        dados["df_ctx"],
        dados_front["hora"],
        dados_front["clima"]
    )

    recomendacoes = recomendar(
        usuario,
        dados,
        features_usuario,
        contexto_score
    )

    salvar_recomendacoes(conn, usuario, recomendacoes)

    if precisa_retreinar(conn, aceitos_novos=0):
        print("🔄 Retreinando modelo...")
        treinar_modelo(conn)
        importlib.reload(model)

    conn.close()

    return jsonify({
        "recomendacoes": recomendacoes
    })

@app.route("/feedback", methods=["POST"])
def feedback_api():
    """
    Chamado quando o usuário confirma um pedido.
    Atualiza rec_aceita = 1 para os itens que ele realmente pediu.

    Body esperado:
    {
      "cpf": "10000000001",
      "produtos": [3, 7]
    }
    """
    dados_front = request.json
    usuario = dados_front.get("cpf")
    produtos = dados_front.get("produtos", [])

    if not usuario or not produtos:
        return {"erro": "Informe cpf e lista de produtos"}, 400

    conn = conectar()

    if not usuario_existe(conn, usuario):
        conn.close()
        return {"erro": "Usuário não cadastrado"}, 400

    atualizar_feedback(conn, usuario, produtos)

    if precisa_retreinar(conn, aceitos_novos=len(produtos)):
        print("Retreinando modelo...")
        treinar_modelo(conn)
        importlib.reload(model)

    conn.close()

    return jsonify({"status": "feedback salvo com sucesso"})


if __name__ == "__main__":
    app.run(debug=True)