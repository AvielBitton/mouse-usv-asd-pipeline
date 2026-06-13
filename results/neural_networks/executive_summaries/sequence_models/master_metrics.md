| Model | Split | Test Acc | Test AUC | HT Recall | HT Prec | HT F1 | WT F1 | Epochs | Params |
|---|---|---|---|---|---|---|---|---|---|
| BiLSTM | dependent | 23.2% | 0.790 | 100.0% | 23.2% | 0.38 | 0.00 | 16 | 148,953 |
| BiLSTM | independent | 45.6% | 0.749 | 100.0% | 27.9% | 0.44 | 0.47 | 16 | 148,953 |
| 1D-CNN | dependent | 50.0% | 0.604 | 68.4% | 27.1% | 0.39 | 0.58 | 22 | 86,041 |
| 1D-CNN | independent | 63.3% | 0.609 | 31.6% | 23.1% | 0.27 | 0.76 | 17 | 86,041 |
| Transformer | dependent | 65.9% | 0.655 | 68.4% | 37.1% | 0.48 | 0.75 | 31 | 72,537 |
| Transformer | independent | 54.4% | 0.675 | 78.9% | 28.8% | 0.42 | 0.62 | 29 | 72,537 |
