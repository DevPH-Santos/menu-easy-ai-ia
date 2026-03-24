import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def carregar_matriz_usuario(conn):
    query = """
    SELECT
    p.fk_cpf_usuario,
    ip.fk_id_prod,
    COUNT(*) as qtd
    FROM Pedidos p
    JOIN Itens_Pedido ip
        ON p.pk_id_ped = ip.fk_id_ped
    GROUP BY p.fk_cpf_usuario, ip.fk_id_prod
    """
    df = pd.read_sql(query, conn)
    matriz = df.pivot_table(
        index="fk_cpf_usuario",
        columns="fk_id_prod",
        values="qtd",
        fill_value=0
    )
    return matriz

def carregar_contexto(conn):
    query = """
    SELECT
    ip.fk_id_prod,
    HOUR(p.ped_hr) AS hora,
    p.ped_clima,
    COUNT(*) as qtd
    FROM Pedidos p
    JOIN Itens_Pedido ip
        ON p.pk_id_ped = ip.fk_id_ped
    GROUP BY
        ip.fk_id_prod,
        HOUR(p.ped_hr),
        p.ped_clima
    """
    df_ctx = pd.read_sql(query, conn)
    df_ctx["ped_clima"] = df_ctx["ped_clima"].str.lower().str.strip()
    return df_ctx

def calcular_contexto_score(df_ctx, hora, clima):
    clima = clima.lower().strip()
    df_filtrado = df_ctx[
        (df_ctx["hora"] == hora) &
        (df_ctx["ped_clima"] == clima)
    ]
    if df_filtrado.empty:
        return df_ctx.groupby("fk_id_prod")["qtd"].sum()
    return df_filtrado.groupby("fk_id_prod")["qtd"].sum()

def carregar_lucro(conn):
    df = pd.read_sql("""
    SELECT pk_id_prod, prod_lucro_porcent
    FROM Produtos
    """, conn)
    return df.set_index("pk_id_prod")["prod_lucro_porcent"]

def carregar_dados(conn):
    matriz = carregar_matriz_usuario(conn)
    sim_users = cosine_similarity(matriz)
    sim_users = pd.DataFrame(sim_users, index=matriz.index, columns=matriz.index)
    matriz_prod = matriz.T
    sim_prod = cosine_similarity(matriz_prod)
    sim_prod = pd.DataFrame(sim_prod, index=matriz_prod.index, columns=matriz_prod.index)
    df_ctx = carregar_contexto(conn)
    lucro = carregar_lucro(conn)
    return {
        "matriz": matriz,
        "sim_users": sim_users,
        "sim_prod": sim_prod,
        "df_ctx": df_ctx,
        "lucro": lucro
    }