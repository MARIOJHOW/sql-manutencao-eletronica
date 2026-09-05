"""
Gera um dataset sintético de chamados de manutenção eletrônica e carrega
em um banco SQLite normalizado (4 tabelas), para permitir queries SQL
reais com JOINs, subqueries, CTEs e window functions.

Reaproveita o mesmo domínio do projeto 'analise-manutencao-eletronica',
agora modelado como um schema relacional em vez de um único CSV.
"""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "dados" / "manutencao.db"

# ---------------------------------------------------------------------
# Dimensões
# ---------------------------------------------------------------------
EQUIPAMENTOS = [
    (1, "Display Digital DD-50", "Sinalização"),
    (2, "Validador de Bilhetes VB-20", "Bilhetagem"),
    (3, "Câmera de Segurança CS-10", "Segurança"),
    (4, "Sistema de Som SS-30", "Sinalização"),
    (5, "GPS Veicular GV-15", "Rastreamento"),
    (6, "Ar Condicionado AC-40", "Climatização"),
    (7, "Roteador de Bordo RB-25", "Conectividade"),
]

TECNICOS = [
    (1, "João Silva"),
    (2, "Marina Costa"),
    (3, "Pedro Almeida"),
    (4, "Fernanda Souza"),
    (5, "Carlos Eduardo"),
]

LINHAS = [(i, f"Linha {i:02d}") for i in range(1, 13)]

TIPOS_FALHA = [
    "Desgaste Mecânico", "Falha Elétrica", "Software/Firmware",
    "Curto-Circuito", "Superaquecimento", "Falha de Sensor", "Oxidação",
]

PRIORIDADES = ["Crítica", "Alta", "Média", "Baixa"]
PRIORIDADE_PESO = [0.10, 0.25, 0.40, 0.25]

# meta de SLA em horas, por prioridade (usada nas queries depois)
SLA_HORAS = {"Crítica": 3, "Alta": 8, "Média": 24, "Baixa": 72}


def gerar_chamados(n=500):
    chamados = []
    inicio = datetime(2023, 1, 1)
    for i in range(1, n + 1):
        data_abertura = inicio + timedelta(
            days=random.randint(0, 545), hours=random.randint(0, 23)
        )
        equipamento_id = random.choice(EQUIPAMENTOS)[0]
        tecnico_id = random.choice(TECNICOS)[0]
        linha_id = random.choice(LINHAS)[0]
        tipo_falha = random.choices(
            TIPOS_FALHA, weights=[22, 18, 15, 13, 12, 12, 8]
        )[0]
        prioridade = random.choices(PRIORIDADES, weights=PRIORIDADE_PESO)[0]

        # Técnicos com desempenho ligeiramente diferente (para a query de
        # performance ter algo real para revelar)
        base_horas = {1: 10, 2: 13, 3: 15, 4: 12, 5: 17}[tecnico_id]
        tempo_resolucao = max(0.5, random.gauss(base_horas, base_horas * 0.35))

        status = "Concluída" if random.random() < 0.792 else "Pendente"
        data_conclusao = (
            data_abertura + timedelta(hours=tempo_resolucao)
            if status == "Concluída"
            else None
        )

        custo_base = {
            "Desgaste Mecânico": 550, "Falha Elétrica": 480,
            "Software/Firmware": 210, "Curto-Circuito": 610,
            "Superaquecimento": 390, "Falha de Sensor": 340,
            "Oxidação": 300,
        }[tipo_falha]
        custo = max(50, random.gauss(custo_base, custo_base * 0.3))

        peca_trocada = "Sim" if random.random() < 0.55 else "Não"

        chamados.append((
            i, data_abertura.isoformat(), equipamento_id, tipo_falha,
            prioridade, tecnico_id, status,
            data_conclusao.isoformat() if data_conclusao else None,
            round(tempo_resolucao, 2) if status == "Concluída" else None,
            round(custo, 2), peca_trocada, linha_id,
        ))
    return chamados


def montar_banco():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE equipamentos (
        id_equipamento INTEGER PRIMARY KEY,
        nome_equipamento TEXT NOT NULL,
        categoria TEXT NOT NULL
    );

    CREATE TABLE tecnicos (
        id_tecnico INTEGER PRIMARY KEY,
        nome_tecnico TEXT NOT NULL
    );

    CREATE TABLE linhas (
        id_linha INTEGER PRIMARY KEY,
        nome_linha TEXT NOT NULL
    );

    CREATE TABLE chamados (
        id_chamado INTEGER PRIMARY KEY,
        data_abertura TEXT NOT NULL,
        id_equipamento INTEGER NOT NULL REFERENCES equipamentos(id_equipamento),
        tipo_falha TEXT NOT NULL,
        prioridade TEXT NOT NULL,
        id_tecnico INTEGER NOT NULL REFERENCES tecnicos(id_tecnico),
        status TEXT NOT NULL,
        data_conclusao TEXT,
        tempo_resolucao_horas REAL,
        custo_estimado REAL NOT NULL,
        peca_trocada TEXT NOT NULL,
        id_linha INTEGER NOT NULL REFERENCES linhas(id_linha)
    );
    """)

    cur.executemany("INSERT INTO equipamentos VALUES (?,?,?)", EQUIPAMENTOS)
    cur.executemany("INSERT INTO tecnicos VALUES (?,?)", TECNICOS)
    cur.executemany("INSERT INTO linhas VALUES (?,?)", LINHAS)
    cur.executemany(
        "INSERT INTO chamados VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        gerar_chamados(500),
    )

    conn.commit()
    conn.close()
    print(f"Banco criado em {DB_PATH} com 500 chamados.")


if __name__ == "__main__":
    montar_banco()
