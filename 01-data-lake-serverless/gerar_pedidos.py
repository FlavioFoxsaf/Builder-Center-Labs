"""Gera pedidos fictícios de uma loja online, um CSV por dia, no layout da camada raw.

Uso:
    python3 gerar_pedidos.py --dias 90 --pedidos-por-dia 20000 --saida ./dados

Saída:
    dados/raw/pedidos/AAAA-MM-DD/pedidos.csv

Os dados vêm "sujos" de propósito (duplicados, valores vazios, status fora do padrão),
para o Glue Job ter o que limpar.
"""
import argparse
import csv
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

CATEGORIAS = {
    "Moda": ["Camiseta", "Vestido", "Tênis", "Boné", "Bolsa"],
    "Casa": ["Luminária", "Almofada", "Jogo de toalhas", "Vaso", "Quadro"],
    "Eletrônicos": ["Fone bluetooth", "Carregador", "Smartwatch", "Caixa de som", "Mouse"],
    "Beleza": ["Perfume", "Hidratante", "Shampoo", "Protetor solar", "Maquiagem"],
    "Esporte": ["Garrafa térmica", "Tapete de yoga", "Corda", "Luvas", "Mochila"],
}
STATUS = ["entregue"] * 7 + ["enviado"] * 2 + ["cancelado"]
STATUS_SUJOS = ["Entregue", "ENTREGUE ", "cancelado ", "Enviado"]


def gerar_dia(dia: date, n: int, clientes: list[str]):
    linhas = []
    for _ in range(n):
        categoria = random.choice(list(CATEGORIAS))
        quantidade = random.choices([1, 2, 3, 4], weights=[70, 20, 7, 3])[0]
        preco = round(random.uniform(19.9, 499.9), 2)
        criado_em = datetime.combine(dia, datetime.min.time()) + timedelta(seconds=random.randint(0, 86399))
        status = random.choice(STATUS)
        if random.random() < 0.03:  # 3% com status fora do padrão
            status = random.choice(STATUS_SUJOS)
        valor = f"{preco * quantidade:.2f}"
        if random.random() < 0.005:  # 0,5% sem valor
            valor = ""
        linhas.append({
            "pedido_id": str(uuid.uuid4()),
            "cliente_id": random.choice(clientes),
            "produto": random.choice(CATEGORIAS[categoria]),
            "categoria": categoria,
            "quantidade": quantidade,
            "valor_total": valor,
            "status": status,
            "criado_em": criado_em.strftime("%Y-%m-%d %H:%M:%S"),
        })
    # 1% de linhas duplicadas (reenvio do sistema)
    linhas += random.sample(linhas, k=max(1, n // 100))
    return linhas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=90)
    p.add_argument("--pedidos-por-dia", type=int, default=20000)
    p.add_argument("--saida", default="./dados")
    p.add_argument("--ate", default=date.today().isoformat(), help="último dia (AAAA-MM-DD)")
    a = p.parse_args()

    random.seed(42)
    clientes = [f"C{i:06d}" for i in range(50000)]
    ultimo = date.fromisoformat(a.ate)
    for i in range(a.dias):
        dia = ultimo - timedelta(days=a.dias - 1 - i)
        pasta = Path(a.saida) / "raw" / "pedidos" / dia.isoformat()
        pasta.mkdir(parents=True, exist_ok=True)
        with open(pasta / "pedidos.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(gerar_dia(dia, 1, clientes)[0].keys()))
            w.writeheader()
            w.writerows(gerar_dia(dia, a.pedidos_por_dia, clientes))
    print(f"{a.dias} arquivos gerados em {Path(a.saida) / 'raw' / 'pedidos'}")


if __name__ == "__main__":
    main()
