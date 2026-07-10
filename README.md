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

## 4. Clusterização e segmentação de clientes (entrega para o cliente)

`notebooks/clusterização/clusterizacao_clientes.ipynb` — segmentação dos clientes por perfil, com a
**taxa média de churn de cada grupo**, para orientar em quais perfis focar a retenção. Carrega os
clusters já calculados por `00_preparacao_dados.ipynb` (K-Means, **K=7**, 22 features) — ou seja, os
mesmos clusters usados internamente pelo modelo final (`25_modelo_final_vencedor.ipynb`), não um
K-Means recalculado à parte. Isso garante que a segmentação de negócio e a feature do modelo preditivo
contam a mesma história.

> **K=7, não K=6:** o valor original (K=6) foi escolhido por bom senso de negócio. Em 2026-07-09,
> depois de sermos superados no Kaggle, testamos sistematicamente vários K contra o score real do
> modelo — K=7 generalizou melhor (recuperou o 1º lugar), mesmo com cotovelo/silhueta praticamente
> idênticos a K=6. Ver seção 3 do notebook de clusterização para os gráficos e a explicação completa.

Resumo dos 7 segmentos (ordenados do maior para o menor risco):

| Cluster | % da base | Taxa de churn | Perfil |
|---|---|---|---|
| 0 | 28,7% | **22,08%** | Mais novos, muitas apólices concentradas em poucos produtos, cobertura básica, renda mais baixa — maior grupo e maior risco |
| 6 | 0,7% | 21,57% | Parecido com o 0, mas nenhum cliente possui imóvel — grupo pequeno, monitorar redundância com o 0 |
| 4 | 5,6% | 18,26% | Menor satisfação/relacionamento de todos + **100% paga em atraso** — atrito já instalado, não imaturidade |
| 2 | 16,1% | 18,04% | Transição entre o cluster 0 e os saudáveis — cobertura ainda majoritariamente básica |
| 1 | 19,2% | 4,42% | Cobertura padrão, bom tempo de casa, renda alta, baixo risco |
| 5 | 13,3% | 2,90% | Premium/padrão misto, maior renda da base, **quase sem filhos/dependentes** |
| 3 | 16,4% | 2,78% | 91,5% cobertura premium, renda alta, **com família** (100% têm filhos) |

**Insight para retenção:** clusters 0, 6, 4 e 2 somam 51,1% da base e concentram o risco acima da
média — mas por motivos diferentes: 0/6/2 são clientes "rasos" (poucos produtos, novos), enquanto o
4 é sobre atrito já instalado (insatisfação + inadimplência), pedindo recuperação de relacionamento
em vez de cross-sell. Os clusters saudáveis (1, 3, 5 — 48,9% da base) se dividem por perfil familiar
dentro do segmento premium (3 = famílias, 5 = sem filhos) — pode orientar qual produto complementar
oferecer a cada um.

---

## 5. Modelagem (`notebooks/modelagem_caue/`)

Pasta com o pipeline de modelagem probabilística de churn. Todos os notebooks de `00` a `25` foram
pensados para rodar em sequência (cada um consome arquivos gerados pelo anterior, salvos em
`dados_processados/`).

### 5.1 Pipeline de preparação

| Notebook | Função |
|---|---|
| `00_preparacao_dados.ipynb` | Carrega `Base_Unificada_Outer.csv` (treino) e `Base_Unificada_Kaggle_Outer.csv` (teste); alinha nomes de coluna entre as duas bases; **corrige um bug de encoding em `regiao`** (4 colunas que representavam a mesma região virando 1); remove leakage/multicolinearidade; faz o split treino/validação **antes** de ajustar qualquer transformação (evita vazamento); ajusta K-Means (**K=7**) só no treino; imputa nulos. Gera `train_model_ready.csv`, `val_model_ready.csv`, `kaggle_model_ready.csv`. |
| `09_experimento_shift_features.ipynb` | Testa remover as features mais associadas ao *distribution shift* (ver 5.3). Decide manter as fortes em churn e remover 4 fracas+shift (`valor_premio_anual`, `km_anual_estimado`, `tempo_medio_resposta_dias`, `ano_veiculo`). |
| `10_feature_engineering.ipynb` | Cria 11 features derivadas (razões/interações, ex. `apolices_por_produto`, `desconto_x_tempo_cliente`). Junto com o `09`, gera o conjunto **`_v2`**: `train_model_ready_v2.csv`, `val_model_ready_v2.csv`, `kaggle_model_ready_v2.csv` — **é este conjunto que alimenta o modelo final**. |

### 5.2 Os 6 modelos treinados + comparação

| Notebook | Modelo | AUC-ROC validação |
|---|---|---|
| `01_logistic_regression_proba.ipynb` | Regressão Logística | 0.8033 |
| `02_random_forest_proba.ipynb` | Random Forest | 0.8196 |
| `03_xgboost_proba.ipynb` | XGBoost | 0.8240 |
| `04_lightgbm_proba.ipynb` | LightGBM | 0.8238 |
| `05_catboost_proba.ipynb` | CatBoost | 0.8254 |
| `06_extra_trees_proba.ipynb` | Extra Trees | 0.8062 |
| `07_comparacao_final.ipynb` | Compara os 6 (curva ROC, tabela) — só entre eles, não é a recomendação de produção | — |

Cada um desses gera `submissions/submission_<modelo>.csv` (colunas `Id`, `probabilidade_churn`) e
salva as probabilidades de validação em `dados_processados/proba_val/<modelo>.csv`. Sozinho, o
Extra Trees é o 2º pior modelo (0.8062) — seu valor só aparece combinado com o Random Forest no
ensemble final (seção 5.4).

### 5.3 Diagnóstico central: *distribution shift*

`08_validacao_adversarial.ipynb` — **o insight mais importante do projeto**. Treina um classificador
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
com bagging 5-fold sobre as features `_v2`, K-Means com **K=7**). Self-contido: não depende de
nenhum notebook arquivado.

| Modelo | AUC-ROC validação (out-of-fold) | Score Kaggle público |
|---|---|---|
| CatBoost tunado sozinho | 0.8263 | 0.7370 |
| Bagging 5-fold CatBoost | 0.8259 | 0.7383 |
| Stacking (7 modelos, meta-modelo) | 0.8257 | 0.7395 |
| Random Forest + Extra Trees (50/50), K=6 | 0.8199 | 0.7456 |
| **Random Forest + Extra Trees (50/50), K=7** | 0.8201 | **0.7465 — vigente** |

A mudança de K=6 para K=7 veio de um teste sistemático (K=3,4,5,6,7,8,10,12) feito em 2026-07-09
depois de perdermos a liderança da competição — nunca tínhamos testado outros valores de K antes.
K=7 generaliza melhor para o Kaggle apesar do AUC de validação praticamente idêntico a K=6 — mais
uma confirmação de que a métrica de validação interna não prevê bem o desempenho real aqui (ver
seção 5.3).

> **Nota de reprodutibilidade:** reexecutar `25_modelo_final_vencedor.ipynb` hoje reproduz um
> resultado um pouco pior (~0.745) do que o oficial (0.7465), porque o `pandas` foi rebaixado de
> 3.0.3 para 2.3.3 como efeito colateral da instalação do MLflow (seção 6) — mesmo com
> `random_state` fixo, isso muda ligeiramente o resultado do bagging. A submissão oficial em
> `submissions/submission_FINAL_vencedor.csv` foi preservada da execução original comprovada no
> Kaggle, não da reexecução mais recente.

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

## 6. MLflow (SageMaker)

Requisito do projeto: os modelos rodam em MLflow. Os notebooks `00`, `01`-`06` e `25` logam
parâmetros, métricas (AUC-ROC) e o modelo treinado no MLflow — tracking server **`equipe5`** do
SageMaker Studio (ARN `arn:aws:sagemaker:us-east-2:906513713169:mlflow-tracking-server/equipe5`).

- **Tracking URI:** cada notebook lê `os.environ.get("MLFLOW_TRACKING_URI", "<ARN do SageMaker>")`
  — ou seja, usa o SageMaker por padrão, mas pode ser sobrescrito por variável de ambiente (útil
  pra testar local sem depender de credenciais AWS).
- **Model Registry:** o notebook `25` registra o ensemble final como **`churn-prt-final`** — um
  wrapper `mlflow.pyfunc.PythonModel` que combina Random Forest + Extra Trees numa única chamada
  `predict()`, servível como um artefato só (necessário pra um endpoint de inferência).
- **Rodando local (sem AWS):** suba um servidor local (`mlflow server --backend-store-uri
  sqlite:///mlflow.db --default-artifact-root ./mlartifacts --host 127.0.0.1 --port 5000`) e defina
  `MLFLOW_TRACKING_URI=http://127.0.0.1:5000` antes de executar os notebooks. Serve como alternativa
  caso o tracking server do SageMaker não esteja acessível.
- **Rodando no SageMaker Studio:** dando `git pull` no ambiente Studio, a *execution role* do domínio
  já deve ter permissão para o tracking server `equipe5` — não precisa trocar nada no código.
- **O que cada run mostra:** além do AUC-ROC, cada modelo (`01`-`06`) e o ensemble final (`25`) loga
  um conjunto completo de métricas de classificação (accuracy, precision, recall, f1, log-loss,
  average precision) e os gráficos de diagnóstico — curva ROC, matriz de confusão, curva
  precisão-recall, curva de calibração e importância de features (top 15) — visíveis direto na aba
  do run no MLflow. Os modelos de boosting (XGBoost/LightGBM/CatBoost) também logam a evolução do
  AUC a cada rodada de treino; Random Forest e Extra Trees logam AUC vs. número de árvores; o
  ensemble final loga o AUC de cada um dos 5 folds do bagging — todas essas séries aparecem como
  gráficos de linha reais (não só um número) na aba de métricas do MLflow.

> **Pacote `mlflow`:** requer Python compatível (a versão 3.14+ do MLflow tem um bug conhecido de
> import em Python 3.14 muito recente — usamos `mlflow==3.12.0` como contorno). Instalar também
> `sagemaker-mlflow` (plugin necessário pra resolver o ARN como tracking URI). **Atenção:** instalar
> o pacote `sagemaker` completo pode rebaixar o `pandas` (viu uma dependência transitiva puxar
> `pandas<3`) — isso já causou uma pequena diferença de reprodutibilidade no modelo final (seção 5.4).
> Se for reinstalar, confira a versão do pandas depois (`pip show pandas`).

---

## 7. Submissão no Kaggle

Competição privada `poli-junior`. Autenticação via `kaggle.json`/token de API (não versionado).
Comando de envio:
```
kaggle competitions submit -c poli-junior -f <arquivo.csv> -m "<mensagem>"
kaggle competitions submissions -c poli-junior   # ver histórico e scores
```
O formato de submissão é livre (sem `sample_submission.csv` oficial) — usamos `Id` (= `cod_individuo`)
e `probabilidade_churn`.

---

## 8. Próximos passos sugeridos

- [x] ~~Tunar hiperparâmetro do Random Forest / Extra Trees do modelo final~~ — feito em 2026-07-09
  (`RandomizedSearchCV`). Resultado: AUC de validação melhorou, mas o score no Kaggle **piorou**
  (0.7465 → 0.7394) — mesma lição do shift, agora confirmada dentro da própria família bagging.
  Parâmetros tunados ficaram em `dados_processados/melhores_params_rf_et.json`, não usados em produção.
- [ ] Investigar se o cluster 6 (K=7, só 0,7% da base) é redundante com o cluster 0 — ver seção 4
  do README e seção 8 do notebook de clusterização.
- [ ] Fixar as versões de `mlflow`/`pandas`/`scikit-learn` em `requirements.txt` — a reinstalação do
  MLflow rebaixou o pandas e mudou levemente a reprodutibilidade do modelo final (seção 6).
- [ ] Investigar com mais profundidade por que boosting generaliza pior que bagging nesta base — pode
  virar um argumento para a PRT Seguros sobre como montar a próxima base de treino/teste.
