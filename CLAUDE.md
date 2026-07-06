# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Insurance customer churn prediction pipeline built in Python/Jupyter. The goal is to predict whether a customer (`churned` column) will cancel their insurance policy, using data from five source tables merged into a unified dataset.

## Environment

- Python virtual environment at `.venv/` — activate with `.venv\Scripts\activate` (Windows)
- Notebooks run in JupyterLab: `jupyter lab` (uses the `.venv` Python kernel)
- AWS S3 data extraction uses `boto3` (credentials in `.aws/`)
- No test suite or linter is configured

## Data Pipeline Architecture

The pipeline flows through three layers stored under `notebooks/bases/`:

```
tabelas_brutas/ (raw CSVs from S3)
    ├── cadastro_clientes.csv       — customer demographics
    ├── contratos_apolices.csv      — policy/contract data (sep=";")
    ├── atendimento_sinistros.csv   — claims/support interactions
    ├── engajamento_marketing.csv   — marketing engagement
    └── churn_.csv                  — churn labels (target)

tabelas_tratadas/ (cleaned versions of each source table)

tabelas_unificadas/ (merged datasets)
    ├── Base_Unificada_Tratada.csv  — inner join (~81,881 rows, 81 cols)
    └── Base_Unificada_Outer.csv    — outer join (100,000 rows, 81 cols)
```

The merge key is `cod_individuo`. During unification, the column is normalized by stripping `IND-` prefix and `.0` suffix.

## Notebook Organization

- `notebooks/Analise_descritiva/` — data cleaning notebooks per table (one per team member)
- `notebooks/Analise_exploratoria/` — EDA and correlation analysis against churn
- `notebooks/bases/tabelas_unificadas/` — table-merging notebook
- `entrypoints/run_training/config.py` — stub entry point for a training pipeline (currently empty)
- `src/config/config.py` — configuration stub (currently empty)

## Key Data Conventions

**Invalid/null sentinels across all tables:**
```python
INVALID_VALUES = {"?", "null", "NULL", "#N/D", "n/a", "N/A", "na", "NA", "none", "", "-", "--"}
```

**Date format:** always normalized to `dd/mm/yyyy` (Brazilian standard). Ambiguous dates default to `dd/mm` ordering.

**Validation ranges used:**
- `idade` (age): 17–96 years. If missing/invalid, calculated from `data_nascimento`.
- `renda_anual`: 10,000–1,000,000 BRL
- `valor_premio_anual`: 100–20,000 BRL
- `valor_cobertura_total`: 30,000–1,200,000 BRL
- `tempo_cliente_dias`: 29–8,001 days. If missing, calculated from `data_primeira_apolice`.

**Categorical encoding applied before unification:**
- `genero`: M→1, F→0
- `estado_civil`: solteiro→1, casado→0
- `tem_filhos` / `pagamento_em_dia`: sim→1, nao→0
- `tipo_cobertura`, `metodo_pagamento`, `canal_aquisicao`, `regiao`, `tipo_veiculo`: one-hot encoded (columns prefixed with category name)

## Running the Notebooks

Open any notebook in JupyterLab. Each notebook is standalone — it reads from `../bases/tabelas_brutas/` or `../bases/tabelas_tratadas/` using relative paths from its own directory.

To re-run the full pipeline in order:
1. `notebooks/Analise_descritiva/cadastro_clientes_trat.ipynb` — clean `cadastro_clientes`
2. `notebooks/Analise_descritiva/trat_caue.ipynb` — clean `contratos_apolices`
3. `notebooks/Analise_descritiva/trat_rodrigo.ipynb` — clean remaining tables
4. `notebooks/bases/tabelas_unificadas/unificacao_base_tratada.ipynb` — merge all tables
5. `notebooks/Analise_exploratoria/Analise_exp.ipynb` — EDA and churn correlation analysis

See `README.md` at the repo root for the full modeling pipeline (`notebooks/modelagem_caue/`),
customer segmentation (`notebooks/clusterização/`), and the final model.
