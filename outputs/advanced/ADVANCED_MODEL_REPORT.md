# 進階推薦模型比較

本實驗在不使用 metadata 的限制下加入 LightGCN、SASRec、GRU4Rec、
time-decayed ItemKNN，以及 LiveRec-like availability proxy。所有模型使用與主要實驗
相同的 chronological split、未看過頻道 targets、fit catalog 與 Top-10 metrics。

## Test 結果

|   cases |   users |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure | model                   |
|--------:|--------:|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|:------------------------|
|  104818 |   53212 |        0.22342 |      0.13148 |          0.27631 |            0.26363 |       12.07110 |              0.08031 | hybrid_a0.75            |
|  104818 |   53212 |        0.21437 |      0.12584 |          0.26510 |            0.36708 |       12.85157 |              0.14585 | item_knn                |
|  104818 |   53212 |        0.20509 |      0.12046 |          0.25333 |            0.43612 |       13.55955 |              0.21592 | time_decayed_item_knn   |
|  104818 |   53212 |        0.19862 |      0.11694 |          0.24539 |            0.40495 |       13.61158 |              0.20307 | item_knn_count_weighted |
|  104818 |   53212 |        0.10286 |      0.05981 |          0.13247 |            0.00870 |        8.37527 |              0.00818 | lightgcn                |
|  104818 |   53212 |        0.09328 |      0.05420 |          0.12049 |            0.00617 |        9.30445 |              0.00162 | bpr                     |
|  104818 |   53212 |        0.06195 |      0.03779 |          0.08209 |            0.00020 |        7.86368 |              0.00000 | recent_popularity       |
|  104818 |   53212 |        0.06068 |      0.03702 |          0.08018 |            0.00023 |        7.66045 |              0.00000 | popularity              |
|  104818 |   53212 |        0.00966 |      0.00637 |          0.01296 |            0.11431 |       18.21740 |              0.72006 | gru4rec                 |
|  104818 |   53212 |        0.00129 |      0.00055 |          0.00164 |            0.10069 |       18.44771 |              0.64670 | liverec_proxy_active_7d |
|  104818 |   53212 |        0.00046 |      0.00021 |          0.00061 |            0.14970 |       19.20634 |              0.80560 | sasrec                  |

## Validation 結果

|   cases |   users |   recall_at_10 |   ndcg_at_10 |   hit_rate_at_10 |   catalog_coverage |   novelty_bits |   long_tail_exposure | model                   |
|--------:|--------:|---------------:|-------------:|-----------------:|-------------------:|---------------:|---------------------:|:------------------------|
|    9435 |    5000 |        0.20911 |      0.12269 |          0.25808 |            0.10980 |       13.41006 |              0.20924 | time_decayed_item_knn   |
|    9435 |    5000 |        0.11492 |      0.06504 |          0.14616 |            0.00434 |        8.42922 |              0.00958 | lightgcn                |
|    9435 |    5000 |        0.00754 |      0.00416 |          0.00943 |            0.03131 |       18.12765 |              0.69734 | gru4rec                 |
|    9435 |    5000 |        0.00105 |      0.00057 |          0.00148 |            0.03135 |       18.22953 |              0.61164 | liverec_proxy_active_7d |
|    9435 |    5000 |        0.00062 |      0.00031 |          0.00085 |            0.03928 |       18.88718 |              0.77196 | sasrec                  |

## 結論

- **沒有新增模型超越 Hybrid 或 binary ItemKNN。** Hybrid NDCG@10 為 0.13148，
  ItemKNN 為 0.12584，仍是前兩名。
- **LightGCN 比 BPR 好，但幅度不足以取代 ItemKNN。** LightGCN NDCG@10 為
  0.05981，相對 BPR 的 0.05420 高約 10.4%，但只有 ItemKNN 的約 47.5%。
- **Time-decayed ItemKNN 是最有用的新增模型。** NDCG@10 為 0.12046，低於
  binary ItemKNN 約 4.3%，但 catalog coverage 從 36.71% 增至 43.61%，且長尾曝光
  從 14.59% 增至 21.59%。近期加權改善多樣性，卻沒有改善主要準確度。
- **SASRec 與 GRU4Rec 不適合直接套用目前 labels。** 訓練資料中的 next-item
  大量是回訪既有頻道，但本任務在 inference 時排除所有已看過頻道，只評估新頻道。
  因此 sequence models 學到的 repeat-consumption 訊號被評估規則刻意移除。很高的
  novelty/long-tail 數值伴隨極低 Recall，代表它們主要推薦了非常冷門但不正確的頻道。
- **LiveRec proxy 不是原始 LiveRec。** 固定資料沒有推薦瞬間的精確 online-channel
  snapshot；本 row 只是把 SASRec 分數限制在 fit period 最後七天出現過的頻道。

這些 deep models 使用預先固定的合理設定，沒有進行與原始模型同規模的超參數 grid。
因此結果足以回答「目前版本是否立即勝過既有四種方法」，答案是否定的；但不能證明
所有可能調參、loss 或 negative sampling 下的 LightGCN/SASRec 永遠較差。

## 固定設定

```json
{
  "outputs_dir": "outputs/advanced",
  "factors": 64,
  "lightgcn_layers": 2,
  "lightgcn_epochs": 10,
  "lightgcn_learning_rate": 0.01,
  "lightgcn_regularization": 0.0001,
  "lightgcn_samples_per_epoch": 250000,
  "sequential_epochs": 8,
  "sequential_batch_size": 512,
  "sequential_learning_rate": 0.001,
  "max_sequence_length": 50,
  "time_decay": 0.1,
  "item_knn_neighbors": 200,
  "item_knn_batch_size": 512,
  "ranking_batch_size": 64
}
```

Test fit-catalog candidate coverage 為 88.0204%。

`liverec_proxy_active_7d` 並非原始 LiveRec：資料不含推薦時刻的精確 availability
snapshot。它重用 SASRec scores，並將 candidates 限制為 fit period 最後七天出現過的
頻道；proxy 以外的 positives 仍計為 misses。
