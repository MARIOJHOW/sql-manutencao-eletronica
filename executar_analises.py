"""
Executa as queries de queries/analises.sql contra dados/manutencao.db,
imprime os resultados no terminal e gera um dashboard (imagens/dashboard.png).
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "dados" / "manutencao.db"
IMG_PATH = BASE_DIR / "imagens" / "dashboard.png"

sns.set_style("whitegrid")


def run(conn, sql, title):
    df = pd.read_sql_query(sql, conn)
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    print(df.to_string(index=False))
    return df


def main():
    conn = sqlite3.connect(DB_PATH)

    df_equip = run(conn, """
        SELECT e.nome_equipamento, e.categoria, COUNT(*) AS total_chamados,
               SUM(CASE WHEN c.status='Concluída' THEN 1 ELSE 0 END) AS concluidos,
               ROUND(100.0*SUM(CASE WHEN c.status='Concluída' THEN 1 ELSE 0 END)/COUNT(*),1) AS taxa_conclusao_pct
        FROM chamados c JOIN equipamentos e ON e.id_equipamento = c.id_equipamento
        GROUP BY e.nome_equipamento, e.categoria ORDER BY taxa_conclusao_pct ASC
    """, "1) Taxa de conclusão por equipamento")

    df_falha = run(conn, """
        SELECT tipo_falha, COUNT(*) AS ocorrencias,
               ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct_do_total
        FROM chamados GROUP BY tipo_falha ORDER BY ocorrencias DESC
    """, "2) Tipos de falha mais frequentes")

    df_sla = run(conn, """
        WITH sla_meta(prioridade, meta_horas) AS (
            VALUES ('Crítica',3), ('Alta',8), ('Média',24), ('Baixa',72)
        )
        SELECT c.prioridade, COUNT(*) AS chamados_concluidos,
               ROUND(AVG(c.tempo_resolucao_horas),2) AS tempo_medio_horas,
               s.meta_horas,
               CASE WHEN AVG(c.tempo_resolucao_horas) <= s.meta_horas THEN 'Dentro da meta' ELSE 'Fora da meta' END AS status_sla
        FROM chamados c JOIN sla_meta s ON s.prioridade = c.prioridade
        WHERE c.status='Concluída'
        GROUP BY c.prioridade, s.meta_horas
        ORDER BY CASE c.prioridade WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Média' THEN 3 ELSE 4 END
    """, "3) Tempo de resolução por prioridade x SLA")

    df_custo = run(conn, """
        SELECT tipo_falha, COUNT(*) AS qtd_chamados,
               ROUND(SUM(custo_estimado),2) AS custo_total,
               ROUND(AVG(custo_estimado),2) AS custo_medio,
               RANK() OVER (ORDER BY SUM(custo_estimado) DESC) AS ranking_custo
        FROM chamados GROUP BY tipo_falha
    """, "4) Custo por tipo de falha (ranqueado)")

    df_tend = run(conn, """
        WITH chamados_por_mes AS (
            SELECT strftime('%Y-%m', data_abertura) AS mes, COUNT(*) AS total_chamados
            FROM chamados GROUP BY mes
        )
        SELECT mes, total_chamados,
               ROUND(AVG(total_chamados) OVER (ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),1) AS media_movel_3_meses
        FROM chamados_por_mes ORDER BY mes
    """, "5) Tendência mensal com média móvel de 3 meses")

    df_tec = run(conn, """
        SELECT t.nome_tecnico, COUNT(*) AS chamados_atendidos,
               ROUND(AVG(c.tempo_resolucao_horas),2) AS tempo_medio_horas,
               RANK() OVER (ORDER BY AVG(c.tempo_resolucao_horas) ASC) AS ranking_eficiencia
        FROM chamados c JOIN tecnicos t ON t.id_tecnico = c.id_tecnico
        WHERE c.status='Concluída'
        GROUP BY t.nome_tecnico ORDER BY ranking_eficiencia
    """, "6) Performance dos técnicos (ranqueada)")

    df_linha = run(conn, """
        SELECT l.nome_linha, COUNT(*) AS qtd_chamados, ROUND(SUM(c.custo_estimado),2) AS custo_total
        FROM chamados c JOIN linhas l ON l.id_linha = c.id_linha
        GROUP BY l.nome_linha
        HAVING SUM(c.custo_estimado) > (
            SELECT AVG(custo_por_linha) FROM (
                SELECT SUM(custo_estimado) AS custo_por_linha FROM chamados GROUP BY id_linha
            )
        )
        ORDER BY custo_total DESC
    """, "7) Linhas com custo acima da média geral")

    # ---------------- Dashboard ----------------
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Dashboard SQL — Manutenção Eletrônica", fontsize=16, fontweight="bold")

    sns.barplot(data=df_equip, y="nome_equipamento", x="taxa_conclusao_pct", ax=axes[0, 0], color="#4C72B0")
    axes[0, 0].set_title("Taxa de conclusão por equipamento (%)")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("")

    sns.barplot(data=df_falha, y="tipo_falha", x="ocorrencias", ax=axes[0, 1], color="#DD8452")
    axes[0, 1].set_title("Chamados por tipo de falha")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("")

    sns.barplot(data=df_sla, x="prioridade", y="tempo_medio_horas", ax=axes[0, 2], color="#55A868")
    axes[0, 2].set_title("Tempo médio de resolução por prioridade (h)")
    axes[0, 2].set_xlabel("")
    axes[0, 2].set_ylabel("")

    sns.barplot(data=df_custo.sort_values("custo_total", ascending=False), y="tipo_falha", x="custo_total", ax=axes[1, 0], color="#C44E52")
    axes[1, 0].set_title("Custo total por tipo de falha (R$)")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("")

    axes[1, 1].plot(df_tend["mes"], df_tend["total_chamados"], marker="o", label="Chamados/mês")
    axes[1, 1].plot(df_tend["mes"], df_tend["media_movel_3_meses"], marker="o", label="Média móvel 3m")
    axes[1, 1].set_title("Tendência mensal de chamados")
    axes[1, 1].tick_params(axis="x", rotation=90, labelsize=7)
    axes[1, 1].legend(fontsize=8)

    sns.barplot(data=df_tec, y="nome_tecnico", x="tempo_medio_horas", ax=axes[1, 2], color="#8172B2")
    axes[1, 2].set_title("Tempo médio de resolução por técnico (h)")
    axes[1, 2].set_xlabel("")
    axes[1, 2].set_ylabel("")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    IMG_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(IMG_PATH, dpi=140)
    print(f"\nDashboard salvo em {IMG_PATH}")

    conn.close()


if __name__ == "__main__":
    main()
