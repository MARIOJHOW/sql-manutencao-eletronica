-- =====================================================================
-- Análise de Manutenção Eletrônica — Queries SQL
-- Schema: equipamentos, tecnicos, linhas, chamados (ver dados/schema.sql)
-- Compatível com SQLite (usado para gerar os resultados do README);
-- os comentários indicam ajustes triviais para PostgreSQL quando houver.
-- =====================================================================


-- 1) TAXA DE CONCLUSÃO POR EQUIPAMENTO
-- JOIN simples + agregação condicional.
-- ---------------------------------------------------------------------
SELECT
    e.nome_equipamento,
    e.categoria,
    COUNT(*) AS total_chamados,
    SUM(CASE WHEN c.status = 'Concluída' THEN 1 ELSE 0 END) AS concluidos,
    ROUND(
        100.0 * SUM(CASE WHEN c.status = 'Concluída' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS taxa_conclusao_pct
FROM chamados c
JOIN equipamentos e ON e.id_equipamento = c.id_equipamento
GROUP BY e.nome_equipamento, e.categoria
ORDER BY taxa_conclusao_pct ASC;


-- 2) TIPOS DE FALHA MAIS FREQUENTES, COM % DO TOTAL
-- Window function (SUM() OVER) para calcular o percentual sem subquery.
-- ---------------------------------------------------------------------
SELECT
    tipo_falha,
    COUNT(*) AS ocorrencias,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_do_total
FROM chamados
GROUP BY tipo_falha
ORDER BY ocorrencias DESC;


-- 3) TEMPO DE RESOLUÇÃO POR PRIORIDADE X META DE SLA
-- Subquery para trazer a meta de SLA por prioridade e comparar.
-- ---------------------------------------------------------------------
WITH sla_meta (prioridade, meta_horas) AS (
    VALUES
        ('Crítica', 3),
        ('Alta', 8),
        ('Média', 24),
        ('Baixa', 72)
)
SELECT
    c.prioridade,
    COUNT(*) AS chamados_concluidos,
    ROUND(AVG(c.tempo_resolucao_horas), 2) AS tempo_medio_horas,
    s.meta_horas,
    CASE
        WHEN AVG(c.tempo_resolucao_horas) <= s.meta_horas THEN 'Dentro da meta'
        ELSE 'Fora da meta'
    END AS status_sla
FROM chamados c
JOIN sla_meta s ON s.prioridade = c.prioridade
WHERE c.status = 'Concluída'
GROUP BY c.prioridade, s.meta_horas
ORDER BY
    CASE c.prioridade
        WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2
        WHEN 'Média' THEN 3 ELSE 4
    END;


-- 4) CUSTO POR TIPO DE FALHA, RANQUEADO
-- Window function RANK() para ordenar sem precisar de ORDER BY externo.
-- ---------------------------------------------------------------------
SELECT
    tipo_falha,
    COUNT(*) AS qtd_chamados,
    ROUND(SUM(custo_estimado), 2) AS custo_total,
    ROUND(AVG(custo_estimado), 2) AS custo_medio,
    RANK() OVER (ORDER BY SUM(custo_estimado) DESC) AS ranking_custo
FROM chamados
GROUP BY tipo_falha;


-- 5) TENDÊNCIA MENSAL DE CHAMADOS, COM MÉDIA MÓVEL DE 3 MESES
-- Window function com frame (ROWS BETWEEN) — o tipo de query que
-- normalmente não dá pra fazer só com Pandas de forma tão direta.
-- ---------------------------------------------------------------------
WITH chamados_por_mes AS (
    SELECT
        strftime('%Y-%m', data_abertura) AS mes,
        COUNT(*) AS total_chamados
    FROM chamados
    GROUP BY mes
)
SELECT
    mes,
    total_chamados,
    ROUND(
        AVG(total_chamados) OVER (
            ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 1
    ) AS media_movel_3_meses
FROM chamados_por_mes
ORDER BY mes;


-- 6) PERFORMANCE DOS TÉCNICOS, RANQUEADA
-- JOIN + window function RANK() particionada seria por categoria;
-- aqui rankeamos globalmente por tempo médio de resolução.
-- ---------------------------------------------------------------------
SELECT
    t.nome_tecnico,
    COUNT(*) AS chamados_atendidos,
    ROUND(AVG(c.tempo_resolucao_horas), 2) AS tempo_medio_horas,
    RANK() OVER (ORDER BY AVG(c.tempo_resolucao_horas) ASC) AS ranking_eficiencia
FROM chamados c
JOIN tecnicos t ON t.id_tecnico = c.id_tecnico
WHERE c.status = 'Concluída'
GROUP BY t.nome_tecnico
ORDER BY ranking_eficiencia;


-- 7) LINHAS DE ÔNIBUS COM CUSTO ACIMA DA MÉDIA GERAL (subquery correlata)
-- Usa uma subquery no WHERE para comparar cada linha contra a média global.
-- ---------------------------------------------------------------------
SELECT
    l.nome_linha,
    COUNT(*) AS qtd_chamados,
    ROUND(SUM(c.custo_estimado), 2) AS custo_total
FROM chamados c
JOIN linhas l ON l.id_linha = c.id_linha
GROUP BY l.nome_linha
HAVING SUM(c.custo_estimado) > (
    SELECT AVG(custo_por_linha) FROM (
        SELECT SUM(custo_estimado) AS custo_por_linha
        FROM chamados
        GROUP BY id_linha
    )
)
ORDER BY custo_total DESC;
