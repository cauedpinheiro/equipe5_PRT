# Experimentos descartados

Notebooks de investigação que **não superaram** o modelo final (`../25_modelo_final_vencedor.ipynb`,
score no Kaggle público = 0.7456). Mantidos aqui só como histórico — para quem herdar o projeto não
perder tempo tentando de novo algo que já foi testado e não funcionou.

| Notebook | O que testou | Resultado |
|---|---|---|
| `08_blending.ipynb` | Média simples dos 3 boosting (XGB+LGBM+CatBoost) | Kaggle 0.7366 — pior que o final |
| `11_tuning_hiperparametros.ipynb` | RandomizedSearchCV em CatBoost/XGBoost/LightGBM | Melhorou os 3 modelos individualmente, mas nenhum deles entrou no ensemble final |
| `12_blending_tuned.ipynb` | Blend dos modelos já tunados do notebook 11 | Pior que CatBoost tunado sozinho |
| `13_auditoria_shift.ipynb` | Procurou mais bugs de encoding tipo o da `regiao` | Não achou nenhum do mesmo porte; achou 3 colunas fracas+shift (usadas só no notebook 14, que foi abandonado) |
| `14_pipeline_v3_transdutivo.ipynb` | Ajustar imputer/scaler/K-Means com treino+Kaggle juntos (sem vazar rótulo) | Kaggle 0.7368 — não ajudou |
| `15_importance_weighting.ipynb` | Dar mais peso a linhas de treino "parecidas com Kaggle" (propensity score) | Piorou a validação, não foi submetido |
| `16_catboost_categoricas_nativas.ipynb` | CatBoost sem one-hot, usando `cat_features` nativo | Kaggle 0.7354 — one-hot generalizou melhor |
| `17_bagging_5fold.ipynb` | Bagging 5-fold do modelo de categóricas nativas | Kaggle 0.7361 |
| `18_kprototypes.ipynb` | Clusterização K-Prototypes (dados mistos) em vez de K-Means | Kaggle 0.7368 |
| `19_bagging_onehot_5fold.ipynb` | Bagging 5-fold CatBoost one-hot | Kaggle 0.7383 — melhor resultado da época, depois superado |
| `20_bagging_xgb_onehot.ipynb` | Mesmo bagging, com XGBoost | OOF 0.8249, usado só para blend (abaixo) |
| `21_bagging_10seed.ipynb` | Bagging com 10 modelos (2 seeds × 5 folds) | Kaggle 0.7382 — bagging já tinha saturado |
| `22_tuning_amplo_catboost.ipynb` | Busca de hiperparâmetro incluindo `bootstrap_type`, `border_count` | Pior que os parâmetros já encontrados no notebook 11 |
| `23_stacking.ipynb` | Meta-modelo (Logistic Regression) sobre 7 modelos base | Kaggle 0.7395 — chegou perto, mas simples média de Random Forest + Extra Trees venceu |
| `24_ensemble_final.ipynb` | "Final" de uma rodada anterior — média de 5 modelos (incluía boosting) | Kaggle 0.7396 — superado pelo `25` (só RF + Extra Trees, sem boosting) |

**Achado central que motivou boa parte dessas tentativas:** existe um *distribution shift* real
entre a base de treino e a base de teste do Kaggle (ver `08_validacao_adversarial.ipynb`, mantido na
pasta principal). A maior parte destes experimentos tentou atacar esse shift diretamente e não
conseguiu — o que funcionou, no fim, foi trocar boosting por modelos de bagging mais aleatorizados
(ver `25_modelo_final_vencedor.ipynb`).
