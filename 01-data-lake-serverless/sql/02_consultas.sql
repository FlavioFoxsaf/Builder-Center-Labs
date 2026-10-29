-- A) Faturamento por categoria em 30 dias, direto no CSV (tabela criada pelo crawler)
-- (TRY_CAST em cima de varchar funciona qualquer que seja o tipo que o crawler inferiu)
SELECT categoria, SUM(TRY_CAST(CAST(valor_total AS varchar) AS decimal(10,2))) AS faturamento
FROM loja_datalake.raw_pedidos
WHERE TRY_CAST(CAST(criado_em AS varchar) AS timestamp) >= TIMESTAMP '2026-09-29 00:00:00'
GROUP BY categoria
ORDER BY faturamento DESC;

-- B) A mesma pergunta no Parquet particionado
SELECT categoria, SUM(valor_total) AS faturamento
FROM loja_datalake.pedidos
WHERE dt BETWEEN '2026-09-29' AND '2026-10-28'
GROUP BY categoria
ORDER BY faturamento DESC;

-- C) Taxa de cancelamento por semana
SELECT date_trunc('week', criado_em) AS semana,
       ROUND(100.0 * COUNT_IF(status = 'cancelado') / COUNT(*), 2) AS pct_cancelados
FROM loja_datalake.pedidos
WHERE dt >= '2026-08-01'
GROUP BY 1
ORDER BY 1;
