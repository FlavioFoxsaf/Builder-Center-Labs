"""Simula localmente a conversão CSV -> Parquet do Glue Job e mede o volume
que uma consulta de "faturamento por categoria nos últimos 30 dias" precisaria ler.

Uso: python3 medir_local.py ./dados
"""
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

base = Path(sys.argv[1])
raw = sorted((base / "raw" / "pedidos").glob("*/pedidos.csv"))
csv_bytes = sum(f.stat().st_size for f in raw)

df = pd.concat((pd.read_csv(f, dtype=str, keep_default_na=False) for f in raw), ignore_index=True)
linhas_brutas = len(df)
df["status"] = df["status"].str.strip().str.lower()
df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce")
df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").astype("Int32")
df["criado_em"] = pd.to_datetime(df["criado_em"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
df = df[df["valor_total"].notna() & df["criado_em"].notna()]
df = df[df["status"].isin(["entregue", "enviado", "cancelado"])]
df = df.drop_duplicates("pedido_id")
df["dt"] = df["criado_em"].dt.strftime("%Y-%m-%d")

out = base / "processed" / "pedidos"
for dt, parte in df.groupby("dt"):
    pasta = out / f"dt={dt}"
    pasta.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(parte.drop(columns="dt"), preserve_index=False),
                   pasta / "part-0000.snappy.parquet", compression="snappy")

pq_files = sorted(out.glob("dt=*/*.parquet"))
pq_bytes = sum(f.stat().st_size for f in pq_files)

ultimos30 = sorted({f.parent.name for f in pq_files})[-30:]
lidos = 0
for f in pq_files:
    if f.parent.name not in ultimos30:
        continue
    meta = pq.ParquetFile(f).metadata
    for rg in range(meta.num_row_groups):
        for c in range(meta.num_columns):
            col = meta.row_group(rg).column(c)
            if col.path_in_schema in ("categoria", "valor_total"):
                lidos += col.total_compressed_size

mb = lambda b: b / 1024 / 1024
print(f"linhas brutas: {linhas_brutas:,} | linhas limpas: {len(df):,} | removidas: {linhas_brutas - len(df):,}")
print(f"CSV total (raw):           {mb(csv_bytes):8.1f} MB  ({len(raw)} arquivos)")
print(f"Parquet total (processed): {mb(pq_bytes):8.1f} MB  ({len(pq_files)} arquivos)")
print(f"Consulta 30 dias em CSV:   {mb(csv_bytes):8.1f} MB lidos (sem partição, todas as colunas)")
print(f"Consulta 30 dias Parquet:  {mb(lidos):8.2f} MB lidos (30 partições, 2 colunas)")
print(f"Redução: {csv_bytes / lidos:,.0f}x menos dados lidos")
