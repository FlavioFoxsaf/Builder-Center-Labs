CREATE EXTERNAL TABLE loja_datalake.pedidos (
  pedido_id    string,
  cliente_id   string,
  produto      string,
  categoria    string,
  quantidade   int,
  valor_total  decimal(10,2),
  status       string,
  criado_em    timestamp
)
PARTITIONED BY (dt string)
STORED AS PARQUET
LOCATION 's3://SEU_BUCKET/processed/pedidos/'
TBLPROPERTIES (
  'projection.enabled'          = 'true',
  'projection.dt.type'          = 'date',
  'projection.dt.format'        = 'yyyy-MM-dd',
  'projection.dt.range'         = '2026-01-01,NOW',
  'projection.dt.interval'      = '1',
  'projection.dt.interval.unit' = 'DAYS',
  'storage.location.template'   = 's3://SEU_BUCKET/processed/pedidos/dt=${dt}/'
);
