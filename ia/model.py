import pandas as pd
import joblib
import os

BASE_DIR = os.path.dirname(__file__)

# carregar modelos
rf = joblib.load(os.path.join(BASE_DIR, "rf_model.pkl"))
gb = joblib.load(os.path.join(BASE_DIR, "gb_model.pkl"))
xgb = joblib.load(os.path.join(BASE_DIR, "xgb_model.pkl"))
colunas = joblib.load(os.path.join(BASE_DIR, "features.pkl"))


def normalizar(s):
    return (s - s.min()) / (s.max() - s.min() + 1e-9)


def recomendar(usuario, dados, features_usuario, contexto_score):

    matriz = dados["matriz"]
    sim_users = dados["sim_users"]
    sim_prod = dados["sim_prod"]
    lucro_score = dados["lucro"]

    # usuário novo (cold start)
    if usuario not in matriz.index:
        populares = matriz.sum().sort_values(ascending=False)
        return populares.head(3).index.tolist()

    # usuários semelhantes
    users_similares = sim_users[usuario].sort_values(ascending=False)[1:6]
    score_usuario = matriz.loc[users_similares.index].sum()

    # similaridade entre produtos
    score_produto = sim_prod.mean(axis=1)

    # normalização
    score_usuario = normalizar(score_usuario)
    score_produto = normalizar(score_produto)
    contexto_score = normalizar(contexto_score)
    lucro_score = normalizar(lucro_score)

    # remover produtos já consumidos
    ja_consumidos = matriz.loc[usuario]
    ja_consumidos = ja_consumidos[ja_consumidos > 0].index

    candidatos = score_usuario.sort_values(ascending=False).head(15).index
    candidatos = [p for p in candidatos if p not in ja_consumidos]

    # fallback se ficar vazio
    if len(candidatos) == 0:
        candidatos = matriz.columns

    scores = {}

    # ranking com IA
    for produto in candidatos:

        features = {
            "idade_usuario": features_usuario["idade_usuario"],
            "hora": features_usuario["hora"],
            "ped_qtd_pessoas_mesa": features_usuario["ped_qtd_pessoas_mesa"],
            "ped_tem_promocao": features_usuario["ped_tem_promocao"],
            "fk_id_prod": produto,
            "score_usuario": score_usuario.get(produto, 0),
            "score_produto": score_produto.get(produto, 0),
            "contexto_score": contexto_score.get(produto, 0),
            "lucro_score": lucro_score.get(produto, 0),
        }

        features = pd.DataFrame([features])

        # clima (one-hot igual treino)
        clima_col = f"ped_clima_{features_usuario['ped_clima']}"
        if clima_col in colunas:
            features[clima_col] = 1

        # alinhar colunas
        features = features.reindex(columns=colunas, fill_value=0)

        # ENSEMBLE
        prob_rf = rf.predict_proba(features)[0][1]
        prob_gb = gb.predict_proba(features)[0][1]
        prob_xgb = xgb.predict_proba(features)[0][1]

        prob_final = (prob_rf + prob_gb + prob_xgb) / 3

        # SCORE FINAL
        score_final = (
            0.8 * prob_final +
            0.2 * contexto_score.get(produto, 0)
        )

        scores[produto] = score_final

    # retorna top 3
    return sorted(scores, key=scores.get, reverse=True)[:3]