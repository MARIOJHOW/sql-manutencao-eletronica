-- Schema relacional do banco manutencao.db
-- 1 tabela fato (chamados) + 3 tabelas de dimensão

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
    prioridade TEXT NOT NULL,          -- Crítica, Alta, Média, Baixa
    id_tecnico INTEGER NOT NULL REFERENCES tecnicos(id_tecnico),
    status TEXT NOT NULL,              -- Concluída, Pendente
    data_conclusao TEXT,
    tempo_resolucao_horas REAL,
    custo_estimado REAL NOT NULL,
    peca_trocada TEXT NOT NULL,        -- Sim, Não
    id_linha INTEGER NOT NULL REFERENCES linhas(id_linha)
);
