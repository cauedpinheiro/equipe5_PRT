# PRT Seguros — Predição de Probabilidade de Churn

Projeto da Equipe 5 (Poli Júnior) para a **PRT Seguros**: prever a **probabilidade (0 a 1)** de um
cliente cancelar a apólice (`churned`), a partir de dados cadastrais, de contrato, de sinistros/
atendimento e de engajamento de marketing.

O Kaggle (`poli-junior`) é usado só como **benchmark externo de verificação** dos modelos — não é o
entregável em si. O entregável real é o pipeline de dados + os modelos + o modelo final, para
handoff à PRT Seguros.

> **Como manter este README:** sempre que um notebook for criado, movido, apagado ou um resultado
> mudar, atualize a seção correspondente aqui. Ele é a fonte única de verdade sobre o estado atual
> do repositório — mais atualizado que o histórico de conversa ou a memória de qualquer pessoa.

---

## 1. Time e organização

Cada integrante trabalhou numa pasta própria dentro de `notebooks/`:

| Pasta | Integrante | Conteúdo |
|---|---|---|
| `modelagem_caue/` | Caue | Pipeline de modelagem final (00 a 25) — **a que este README documenta em detalhe** |
| `modelagem_rodrigo/` | Rodrigo ("Cabo") | Modelo XGBoost próprio + submissões (`xgboost_clusters_churn_cabo_1/2.ipynb`) — **não editar, pasta de outro integrante** |
| `Analise_descritiva/` | Caue + Rodrigo | Limpeza de cada tabela bruta (ver seção 3) |
| `Analise_exploratoria/` | Compartilhado | Análise exploratória / correlação com churn |

Repositório Git: `github.com/cauedpinheiro/equipe5_PRT` (branch `main`).

---

## 2. Ambiente

- Python via `.venv/` na raiz do projeto (ative com `.venv\Scripts\activate` no Windows).
- `requirements.txt` cobre o essencial (pandas, numpy, scikit-learn, xgboost, matplotlib, seaborn,
  boto3, jupyterlab) — **mas não inclui `catboost`, `lightgbm` nem `kmodes`**, usados nos notebooks
  `05`, `04`/`17`(arquivado) e `18`(arquivado) respectivamente. Instale à parte:
  ```
  pip install catboost lightgbm kmodes
  ```
- Extração de dados brutos via AWS S3 (`boto3`, credenciais em `.aws/`).
- Sem suíte de testes ou linter configurado.

---

## 3. Pipeline de dados

Fluxo em 3 camadas dentro de `notebooks/bases/`:

```
tabelas_brutas/          (CSVs brutos extraídos do S3 — base de TREINO)
    ├── cadastro_clientes.csv
    ├── contratos_apolices.csv      (separador ";")
    ├── atendimento_sinistros.csv
    ├── engajamento_marketing.csv
    └── churn_.csv                  (rótulo target)

tabelas_tratadas/        (versões limpas de cada tabela — treino)

tabelas_unificadas/
    ├── Base_Unificada_Tratada.csv  — inner join (~81.881 linhas)
    └── Base_Unificada_Outer.csv    — outer join (100.000 linhas) ← USADA NA MODELAGEM

bases_kaggle/             (mesmo fluxo, só que para a base de TESTE do Kaggle)
    ├── brutas/            (4 tabelas brutas, sem churn — é o que se quer prever)
    ├── tratadas/
    └── Base_Unificada_Kaggle_Outer.csv  ← USADA COMO TESTE FINAL
```

Chave de junção: `cod_individuo` (normalizado removendo prefixo `IND-` e sufixo `.0`).

### Ordem de execução da pipeline de dados

1. `notebooks/Analise_descritiva/cadastro_clientes_trat.ipynb` — limpa `cadastro_clientes`.
2. `notebooks/Analise_descritiva/trat_caue.ipynb` — limpa `contratos_apolices` (treino) e re-gera as
   bases unificadas ao final.
3. `notebooks/Analise_descritiva/trat_rodrigo.ipynb` — limpa `atendimento_sinistros` e
   `engajamento_marketing`.
4. `notebooks/bases/tabelas_unificadas/unificacao_base_tratada.ipynb` — faz o merge final (inner
   join) → `Base_Unificada_Tratada.csv`. *(Renomeado de `Untitled.ipynb` em 2026-07-04 para ficar
   claro o que o notebook faz.)*
5. `notebooks/Analise_exploratoria/Analise_exp.ipynb` e `analise_exploratoria.ipynb` — EDA e
   correlação com churn.

### Pipeline paralela para a base Kaggle (teste)

- `notebooks/Analise_descritiva/trat_caue2.ipynb` — limpa `cadastro_clientes_kaggle` e
  `contratos_apolices_kaggle` → `bases_kaggle/tratadas/`.
- `notebooks/bases/bases_kaggle/unificacao_kaggle_outer.ipynb` — outer join das 4 tabelas kaggle
  tratadas → `Base_Unificada_Kaggle_Outer.csv`.

### Convenções de dados (ver também `CLAUDE.md`)

- Sentinelas de valor inválido: `{"?", "null", "NULL", "#N/D", "n/a", "N/A", "na", "NA", "none", "", "-", "--"}`
- Datas normalizadas para `dd/mm/yyyy`.
- Faixas de validação: `idade` 17–96, `renda_anual` 10k–1M, `valor_premio_anual` 100–20k,
  `valor_cobertura_total` 30k–1.2M, `tempo_cliente_dias` 29–8001.
- Binários: `genero` (M→1,F→0), `estado_civil` (solteiro→1,casado→0), `tem_filhos`/`pagamento_em_dia`
  (sim→1,nao→0).
- Categóricas de alta cardinalidade (`tipo_cobertura`, `metodo_pagamento`, `canal_aquisicao`,
  `regiao`, `tipo_veiculo`, `segmento`) → one-hot antes da unificação.

---

## 4. Clusterização

`notebooks/clusterização/clusterizacao_clientes.ipynb` — segmentação K-Means dos clientes usando 26
features correlacionadas com churn (|corr| > 0.01). Método do cotovelo + silhueta apontam para
**K=6**. Cruza os clusters com a taxa de churn para dar um perfil de risco por segmento. Essa
lógica é reproduzida (com ajustes) dentro do `notebooks/modelagem_caue/00_preparacao_dados.ipynb`
para gerar a feature `cluster` usada nos modelos.

---

## 5. Modelagem (`notebooks/modelagem_caue/`)

Pasta com o pipeline de modelagem probabilística de churn. Todos os notebooks de `00` a `25` foram
pensados para rodar em sequência (cada um consome arquivos gerados pelo anterior, salvos em
`dados_processados/`).

### 5.1 Pipeline de preparação

| Notebook | Função |
|---|---|
| `00_preparacao_dados.ipynb` | Carrega `Base_Unificada_Outer.csv` (treino) e `Base_Unificada_Kaggle_Outer.csv` (teste); alinha nomes de coluna entre as duas bases; **corrige um bug de encoding em `regiao`** (4 colunas que representavam a mesma região virando 1); remove leakage/multicolinearidade; faz o split treino/validação **antes** de ajustar qualquer transformação (evita vazamento); ajusta K-Means (K=6) só no treino; imputa nulos. Gera `train_model_ready.csv`, `val_model_ready.csv`, `kaggle_model_ready.csv`. |
| `09_experimento_shift_features.ipynb` | Testa remover as features mais associadas ao *distribution shift* (ver 5.3). Decide manter as fortes em churn e remover 4 fracas+shift (`valor_premio_anual`, `km_anual_estimado`, `tempo_medio_resposta_dias`, `ano_veiculo`). |
| `10_feature_engineering.ipynb` | Cria 11 features derivadas (razões/interações, ex. `apolices_por_produto`, `desconto_x_tempo_cliente`). Junto com o `09`, gera o conjunto **`_v2`**: `train_model_ready_v2.csv`, `val_model_ready_v2.csv`, `kaggle_model_ready_v2.csv` — **é este conjunto que alimenta o modelo final**. |

### 5.2 Os 5 modelos pedidos + comparação

| Notebook | Modelo | AUC-ROC validação |
|---|---|---|
| `01_logistic_regression_proba.ipynb` | Regressão Logística | 0.8033 |
| `02_random_forest_proba.ipynb` | Random Forest | 0.8196 |
| `03_xgboost_proba.ipynb` | XGBoost | 0.8240 |
| `04_lightgbm_proba.ipynb` | LightGBM | 0.8238 |
| `05_catboost_proba.ipynb` | CatBoost | 0.8254 |
| `06_comparacao_final.ipynb` | Compara os 5 (curva ROC, tabela) | — |

Cada um desses gera `submissions/submission_<modelo>.csv` (colunas `Id`, `probabilidade_churn`) e
salva as probabilidades de validação em `dados_processados/proba_val/<modelo>.csv`.

### 5.3 Diagnóstico central: *distribution shift*

`07_validacao_adversarial.ipynb` — **o insight mais importante do projeto**. Treina um classificador
para prever "essa linha é do treino ou do Kaggle?" usando só as features. Resultado: AUC ≈ 0.72,
ou seja, treino e teste têm uma distribuição diferente o suficiente pra um modelo perceber — mesmo
que a média/desvio-padrão de cada feature isolada pareça igual (checado feature a feature). Isso
explica por que o AUC de validação (~0.82) é sempre bem mais alto que o score real no Kaggle (~0.74):
o modelo aprende padrões que não se repetem exatamente do mesmo jeito na base de teste.

Esse diagnóstico motivou boa parte das tentativas documentadas em `experimentos_descartados/`
(tentar corrigir o shift diretamente) — a maioria não funcionou. O que funcionou foi trocar boosting
por modelos de bagging mais aleatorizados (seção 5.4).

### 5.4 Modelo final

**`25_modelo_final_vencedor.ipynb`** — Ensemble **Random Forest + Extra Trees** (média 50/50, cada um
com bagging 5-fold sobre as features `_v2`). Self-contido: não depende de nenhum notebook arquivado.

| Modelo | AUC-ROC validação (out-of-fold) | Score Kaggle público |
|---|---|---|
| CatBoost tunado sozinho | 0.8263 | 0.7370 |
| Bagging 5-fold CatBoost | 0.8259 | 0.7383 |
| Stacking (7 modelos, meta-modelo) | 0.8257 | 0.7395 |
| **Random Forest + Extra Trees (50/50)** | 0.8199 | **0.7456** |

Contraintuitivo: o ensemble final tem AUC de validação **mais baixo** que o CatBoost sozinho, mas
generaliza melhor pro Kaggle. Hipótese (ver notebook `25` para detalhes): boosting ajusta resíduos
sequencialmente e acaba capturando padrões específicos da distribuição de treino, incluindo os
ligados ao shift do item 5.3; bagging com alta aleatoriedade (Extra Trees principalmente) produz
fronteiras de decisão mais suaves e mais robustas a essa diferença de distribuição.

Saída final: `submissions/submission_FINAL_vencedor.csv`.

### 5.5 `experimentos_descartados/`

15 notebooks (`08`, `11`–`24`) com tentativas que **não superaram** o modelo final — categóricas
nativas do CatBoost, K-Prototypes, ajuste transdutivo do imputer/scaler/K-Means, importance
weighting, tuning amplo de hiperparâmetro, stacking com meta-modelo, etc. Cada um está descrito
(o que testou + resultado) no `experimentos_descartados/README.md`. Mantidos como histórico —
consulte antes de repetir uma investigação.

### 5.6 Estrutura de pastas de apoio

```
modelagem_caue/
├── dados_processados/         # datasets prontos p/ modelo + metadados (features escolhidas etc.)
│   └── proba_val/              # probabilidade de validação de cada um dos 5 modelos (p/ blending)
├── submissions/                # 1 CSV por modelo obrigatório + submission_FINAL_vencedor.csv
└── experimentos_descartados/   # notebooks + dados + submissões de tentativas sem sucesso
```

---

## 6. Submissão no Kaggle

Competição privada `poli-junior`. Autenticação via `kaggle.json`/token de API (não versionado).
Comando de envio:
```
kaggle competitions submit -c poli-junior -f <arquivo.csv> -m "<mensagem>"
kaggle competitions submissions -c poli-junior   # ver histórico e scores
```
O formato de submissão é livre (sem `sample_submission.csv` oficial) — usamos `Id` (= `cod_individuo`)
e `probabilidade_churn`.

---

## 7. Próximos passos sugeridos

- [ ] Tunar hiperparâmetro do Random Forest / Extra Trees do modelo final (o `11_tuning_hiperparametros.ipynb`,
  arquivado, tunou CatBoost/XGBoost/LightGBM — os dois modelos do ensemble final ainda usam parâmetros
  não-tunados).
- [ ] Investigar com mais profundidade por que boosting generaliza pior que bagging nesta base — pode
  virar um argumento para a PRT Seguros sobre como montar a próxima base de treino/teste.
