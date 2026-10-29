"""Glue Job: raw (CSV) -> processed (Parquet particionado por dt).

Parâmetros do job:
    --SOURCE_PATH  s3://<bucket>/raw/pedidos/
    --TARGET_PATH  s3://<bucket>/processed/pedidos/
"""
import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "SOURCE_PATH", "TARGET_PATH"])

sc = SparkContext()
glue = GlueContext(sc)
spark = glue.spark_session
job = Job(glue)
job.init(args["JOB_NAME"], args)

# Sobrescreve só as partições (dias) que vierem nesta execução, sem apagar o resto
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# 1. Leitura: tudo como texto. Quem define os tipos somos nós, não a inferência.
bruto = (
    spark.read
    .option("header", "true")
    .option("recursiveFileLookup", "true")
    .csv(args["SOURCE_PATH"])
)

# 2. Limpeza e tipagem
pedidos = (
    bruto
    .withColumn("status", F.lower(F.trim(F.col("status"))))
    .withColumn("quantidade", F.col("quantidade").cast("int"))
    .withColumn("valor_total", F.col("valor_total").cast("decimal(10,2)"))
    .withColumn("criado_em", F.to_timestamp("criado_em", "yyyy-MM-dd HH:mm:ss"))
    .filter(F.col("valor_total").isNotNull() & F.col("criado_em").isNotNull())
    .filter(F.col("status").isin("entregue", "enviado", "cancelado"))
    .dropDuplicates(["pedido_id"])
    # 3. Coluna de partição derivada da data do pedido
    .withColumn("dt", F.date_format("criado_em", "yyyy-MM-dd"))
)

# 4. Escrita: Parquet comprimido, um arquivo por dia (volume pequeno por dia)
(
    pedidos
    .repartition("dt")
    .write
    .mode("overwrite")
    .partitionBy("dt")
    .option("compression", "snappy")
    .parquet(args["TARGET_PATH"])
)

job.commit()
