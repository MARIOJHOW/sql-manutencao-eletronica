# 🗄️ Análise de Manutenção Eletrônica em SQL

![SQL](https://img.shields.io/badge/SQL-SQLite%20%7C%20PostgreSQL--ready-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Status](https://img.shields.io/badge/Status-Completo-success)

## 🎯 Objetivo do Projeto

Modelar um banco de dados relacional a partir de chamados de manutenção de
equipamentos de mobilidade urbana e responder perguntas de negócio usando
**SQL puro** — joins, CTEs, subqueries e window functions — em vez de
Pandas. É a contraparte em banco de dados do projeto
[`analise-manutencao-eletronica`](https://github.com/MARIOJHOW/analise-manutencao-eletronica),
que resolve um domínio parecido usando Python.

## 📁 Estrutura do Projeto

```
sql-manutencao/
│
├── dados/
│   ├── manutencao.db        # Banco SQLite já populado (500 chamados)
│   └── schema.sql           # Definição das 4 tabelas
│
├── queries/
│   └── analises.sql         # 7 queries analíticas comentadas
│
├── imagens/
│   └── dashboard.png        # Dashboard gerado a partir dos resultados
│
├── gerar_banco.py           # Gera os dados sintéticos e monta o banco
├── executar_analises.py     # Roda as queries e gera o dashboard
└── README.md
```

## 🗃️ Modelo de Dados

Banco normalizado em 4 tabelas (1 fato + 3 dimensões), para permitir joins
reais em vez de um único CSV plano:

- **chamados** (fato): cada chamado de manutenção aberto
- **equipamentos** (dimensão): 7 tipos de equipamento, por categoria
- **tecnicos** (dimensão): 5 técnicos responsáveis
- **linhas** (dimensão): 12 linhas de ônibus atendidas

Ver definição completa em [`dados/schema.sql`](dados/schema.sql).

## 🔍 Queries e Insights

Todas as queries estão comentadas em [`queries/analises.sql`](queries/analises.sql).
Técnicas usadas: `JOIN`, `GROUP BY` com agregação condicional, **CTE**
(`WITH`), **subquery correlata**, e **window functions** (`RANK() OVER`,
`SUM() OVER`, `AVG() OVER` com `ROWS BETWEEN`).

### 1. Taxa de conclusão por equipamento
Display Digital DD-50 tem a menor taxa de conclusão entre os equipamentos
(73,8%), abaixo da média geral — candidato a revisão de processo.

### 2. Tipos de falha mais frequentes
"Desgaste Mecânico" responde por 24,8% dos chamados (124 de 500) — o tipo
de falha mais comum, por larga margem.

### 3. Tempo de resolução x meta de SLA
Aqui está o insight mais relevante do projeto: o tempo médio de resolução
é praticamente **igual entre todas as prioridades (~13h)** — ou seja,
chamados "Crítica" não estão sendo resolvidos mais rápido que os de
"Baixa" prioridade. Isso indica que a fila de atendimento não está
de fato priorizando por criticidade, e chamados Crítica/Alta estão fora
da meta de SLA (3h e 8h, respectivamente).

### 4. Custo por tipo de falha
"Desgaste Mecânico" também lidera em custo total (R$ 65.726,31),
reforçando que é o alvo prioritário para um programa de manutenção
preventiva.

### 5. Tendência mensal (média móvel de 3 meses)
Volume de chamados oscila mês a mês sem tendência clara de alta ou queda
ao longo do período analisado (jan/2023–jun/2024).

### 6. Performance dos técnicos
João Silva tem o menor tempo médio de resolução (9,53h), seguido por
Fernanda Souza (11,90h) — uma referência de boas práticas para
treinamento interno.

### 7. Linhas com custo acima da média
6 das 12 linhas concentram custo de manutenção acima da média geral,
com a Linha 02 no topo (R$ 23.301,05).

## 📊 Dashboard

![Dashboard](imagens/dashboard.png)

## 🔧 Tecnologias

- **SQL** (SQLite; queries escritas para serem portáveis para PostgreSQL)
- **Python 3.x** — geração dos dados e orquestração
- **Pandas**, **Matplotlib**, **Seaborn** — leitura dos resultados e dashboard

## 🚀 Como Executar

```bash
pip install pandas matplotlib seaborn

# 1. Gerar o banco de dados sintético
python gerar_banco.py

# 2. Rodar as análises e gerar o dashboard
python executar_analises.py

# 3. (Opcional) Explorar as queries diretamente com o CLI do SQLite
sqlite3 dados/manutencao.db
sqlite> .read queries/analises.sql
```

## 📝 Nota sobre os dados

Dataset sintético, gerado por `gerar_banco.py` para fins de portfólio —
não representa dados reais de nenhuma empresa.

## 👤 Autor

**Mário Sérgio Inácio Júnior**
- LinkedIn: [Mário Sérgio Inácio Júnior](https://www.linkedin.com/in/m%C3%A1rio-s%C3%A9rgioin%C3%A1cio-j%C3%BAnior-026705149)
- GitHub: [github.com/MARIOJHOW](https://github.com/MARIOJHOW)
- Email: mariosergioijr@gmail.com

---
*Projeto desenvolvido como parte da transição de carreira para Análise de Dados e Cloud Computing.*
