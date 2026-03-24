import pandas as pd
import random
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from xgboost import XGBClassifier
import joblib
import os
from bd import conectar

BASE_DIR = os.path.dirname(__file__)

def modelos_existem():
    arquivos = ["rf_model.pkl", "gb_model.pkl", "xgb_model.pkl", "features.pkl"]
    return all(os.path.exists(os.path.join(BASE_DIR, f)) for f in arquivos)

def treino_inicial(conn):
    """
    Usado na primeira vez — quando Recomendacao_Log está vazio.
    Usa Itens_Pedido como positivos (rec_aceita=1)
    e gera negativos sintéticos balanceados (rec_aceita=0).
    """
    print("🚀 Treino inicial com Itens_Pedido...")

    query = """
    SELECT
        u.idade_usuario,
        HOUR(p.ped_hr)          AS hora,
        p.ped_clima,
        p.ped_qtd_pessoas_mesa,
        p.ped_tem_promocao,
        ip.fk_id_prod,
        p.fk_cpf_usuario
    FROM Itens_Pedido ip
    JOIN Pedidos p  ON ip.fk_id_ped  = p.pk_id_ped
    JOIN Usuario u  ON p.fk_cpf_usuario = u.pk_cpf_usuario
    """
    df_pos = pd.read_sql(query, conn)
    df_pos["rec_aceita"] = 1

    # todos os produtos disponíveis
    produtos_disponiveis = pd.read_sql(
        "SELECT pk_id_prod FROM Produtos", conn
    )["pk_id_prod"].tolist()

    # gerar negativos sintéticos balanceados
    negativos = []
    for _, row in df_pos.iterrows():
        # produto diferente do que foi pedido
        negativos_possiveis = [p for p in produtos_disponiveis if p != row["fk_id_prod"]]
        prod_neg = random.choice(negativos_possiveis)
        negativos.append({
            "idade_usuario":         row["idade_usuario"],
            "hora":                  row["hora"],
            "ped_clima":             row["ped_clima"],
            "ped_qtd_pessoas_mesa":  row["ped_qtd_pessoas_mesa"],
            "ped_tem_promocao":      row["ped_tem_promocao"],
            "fk_id_prod":            prod_neg,
            "fk_cpf_usuario":        row["fk_cpf_usuario"],
            "rec_aceita":            0
        })

    df_neg = pd.DataFrame(negativos)
    df = pd.concat([df_pos, df_neg], ignore_index=True)

    print(f"✅ Dataset balanceado — positivos: {len(df_pos)} | negativos: {len(df_neg)}")

    _treinar(df)


def treinar_modelo(conn):
    """
    Retreino com Recomendacao_Log (chamado automaticamente a cada 50 aceitações).
    """
    print("🔄 Retreinando com Recomendacao_Log...")

    query = """
    SELECT
        u.idade_usuario,
        HOUR(p.ped_hr)          AS hora,
        p.ped_clima,
        p.ped_qtd_pessoas_mesa,
        p.ped_tem_promocao,
        r.fk_id_prod,
        r.rec_aceita,
        r.fk_cpf_usuario
    FROM Recomendacao_Log r
    JOIN Usuario u ON r.fk_cpf_usuario = u.pk_cpf_usuario
    JOIN Pedidos p ON p.pk_id_ped = (
        SELECT pk_id_ped FROM Pedidos
        WHERE fk_cpf_usuario = r.fk_cpf_usuario
        ORDER BY ped_data DESC
        LIMIT 1
    )
    """
    df = pd.read_sql(query, conn)

    if df.empty:
        print("⚠️  Recomendacao_Log vazio — pulando retreino.")
        return

    print(f"✅ {len(df)} registros no log.")
    _treinar(df)


def _treinar(df):
    """
    Lógica de treino compartilhada entre treino_inicial e treinar_modelo.
    """
    # limpeza
    df["ped_clima"] = df["ped_clima"].str.lower().str.strip()

    # features extras
    popularidade = df.groupby("fk_id_prod").size()
    df["popularidade_prod"] = df["fk_id_prod"].map(popularidade)

    freq_user_prod = df.groupby(["fk_cpf_usuario", "fk_id_prod"]).size()
    df["freq_usuario_prod"] = df.set_index(["fk_cpf_usuario", "fk_id_prod"]).index.map(freq_user_prod)

    def norm(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    df["popularidade_prod"] = norm(df["popularidade_prod"])
    df["freq_usuario_prod"] = norm(df["freq_usuario_prod"])

    # one-hot clima
    df = pd.get_dummies(df, columns=["ped_clima"], drop_first=False)

    # features finais
    X = df.drop(columns=["rec_aceita", "fk_cpf_usuario"])
    y = df["rec_aceita"]

    print(f"📊 Shape: {X.shape} | Distribuição y:\n{y.value_counts()}")

    # modelos
    rf = RandomForestClassifier(n_estimators=150, random_state=42)
    gb = GradientBoostingClassifier(random_state=42)
    xgb = XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )

    rf.fit(X, y)
    print("✅ RandomForest treinado")
    gb.fit(X, y)
    print("✅ GradientBoosting treinado")
    xgb.fit(X, y)
    print("✅ XGBoost treinado")

    # salvar
    joblib.dump(rf,          os.path.join(BASE_DIR, "rf_model.pkl"))
    joblib.dump(gb,          os.path.join(BASE_DIR, "gb_model.pkl"))
    joblib.dump(xgb,         os.path.join(BASE_DIR, "xgb_model.pkl"))
    joblib.dump(X.columns,   os.path.join(BASE_DIR, "features.pkl"))

    print("🎉 Modelos salvos com sucesso!")


# EXECUÇÃO DIRETA
if __name__ == "__main__":
    conn = conectar()

    if modelos_existem():
        print("📦 .pkl já existem — rodando retreino com log...")
        treinar_modelo(conn)
    else:
        print("📦 Nenhum .pkl encontrado — rodando treino inicial...")
        treino_inicial(conn)

    conn.close()