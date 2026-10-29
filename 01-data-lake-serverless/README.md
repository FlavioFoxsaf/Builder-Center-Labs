# Data lake serverless na AWS (S3, Glue e Athena)

Código da série de artigos no AWS Builder Center:

- Parte 1: arquitetura e decisões
- Parte 2: implementação passo a passo

## Estrutura

```text
gerar_pedidos.py          gera pedidos fictícios (CSV por dia, com dados sujos de propósito)
medir_local.py            simula a conversão CSV -> Parquet localmente e mede o volume lido
glue/csv_to_parquet.py    Glue Job (PySpark): raw CSV -> processed Parquet particionado por dt
iam/                      trust policy e policy de menor privilégio da role do Glue
sql/                      DDL da tabela com partition projection e consultas de comparação
```

## Rodando local

```bash
pip install pandas pyarrow
python3 gerar_pedidos.py --dias 90 --pedidos-por-dia 20000 --ate 2026-10-28 --saida ./dados
python3 medir_local.py ./dados
```

O passo a passo na AWS está na Parte 2 do artigo.

Autor: Flávio Fox, AWS User Group Leader Salvador
