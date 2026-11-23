# Assignment 2 20 分鐘投影片講稿（繁體中文）

投影片檔：`assignment2_20min_zh_tw.pptx`

建議錄影時同時開啟 `workbook.html`；第 9 頁可短暫切到 notebook／repository 做 code walkthrough。

## 1. Twitch 新頻道推薦系統

時間：0:00–0:35（35 秒）

大家好，這個專案研究的是 Twitch 新頻道推薦。我們不是要預測使用者會不會回去看熟悉的實況主，而是根據過去觀看紀錄，推薦十個他從未看過、但未來可能會第一次觀看的頻道。接下來我會依 Assignment 2 的五個部分，說明任務、EDA、模型、評估與相關研究。

## 2. 20 分鐘簡報路線圖

時間：0:35–1:15（40 秒）

這份簡報直接對應五個各五分的評分部分。我會特別把 EDA 和模型選擇連起來，也會討論負面結果，因為 rubric 明確要求結果要合理、失敗也要被解釋。最後的相關工作會說明我們和原始 LiveRec 任務為何不同，因此不能直接比較數字。

## 3. 預測任務

時間：1:15–2:25（70 秒）

輸入是使用者過去看過哪些頻道。模型對訓練期已知的完整頻道庫排序，先排除使用者已看過的項目，再輸出十個頻道。未來第一次觀看的 user-channel pair 才是 positive。這是一個 ranking task，不是星等預測，也不是把所有沒看過的頻道當成真正負評。為了確認個人化是否有價值，我們一定要和全域及近期熱門度比較。

## 4. 資料集

時間：2:25–3:30（65 秒）

資料來自 UCSD 公開的 Twitch dataset，記錄聊天室連線，每十分鐘是一個 time slot。官方 subset 有十萬使用者、十六萬多個頻道與三百零五萬筆互動。品質檢查沒有發現缺失或明顯壞資料；困難不是 cleaning，而是十萬乘十六萬的矩陣幾乎都是空的，而且沒有遊戲類別、語言或文字內容可用。

## 5. EDA：長尾

時間：3:30–4:40（70 秒）

橫軸是頻道熱門度排名，縱軸是互動數，兩邊都是對數尺度。曲線仍下降很多個數量級，說明資料非常長尾。這個觀察直接導出三件事：熱門度是不能省略的 baseline；BPR 必須為大量低資料頻道學 embedding，可能不穩；評估不能只看準確度，還要檢查推薦是否只集中在少數頭部頻道。

## 6. EDA：重複觀看與冷啟動

時間：4:40–5:40（60 秒）

第二個現象是回訪互動逐漸增加。這和原始 LiveRec 的動機一致，但我們刻意研究 discovery，所以重複觀看不算測試 positive。主要 user-item matrix 用 binary，而 count-weighted 只是 ablation。另外約百分之十二的新頻道答案在訓練期完全沒出現，這形成協同過濾無法跨越的候選覆蓋上限。

## 7. 時間切分與有效性

時間：5:40–6:55（75 秒）

資料依時間切成前百分之七十訓練、接著驗證、最後測試。所有 mapping、熱門度、ItemKNN 相似度和 BPR 參數都只從 fit period 建立。驗證集選參數後，用 train 加 validation 重訓，測試只看一次。評估時對完整 catalog 排序，而不是用少量容易的 sampled negatives。因為同一使用者有多個 day cases，信賴區間以 user 為 cluster 做一萬次 paired bootstrap。

## 8. 模型

時間：6:55–8:25（90 秒）

我們比較由簡到繁的四類方法。Popularity 是必要的非個人化基準。ItemKNN 用共同觀眾計算頻道相似度，直接保留局部 co-view 關係。BPR 使用 pairwise objective，讓看過的頻道分數高於抽到的未觀看頻道。Hybrid 先對每位使用者的 eligible candidates 標準化兩種分數再混合。這裡不直接用一般分類器，是因為負例數量巨大，而且未互動不是可靠的負標籤；我們真正要最佳化的是前十名排序。

## 9. 程式與架構

時間：8:25–9:20（55 秒）

程式由 YAML 固定 seed 和搜尋空間，DuckDB 負責大型資料處理，再訓練稀疏 ItemKNN 與 BPR。ItemKNN 用 block multiplication，避免建立十六萬乘十六萬的 dense matrix，只保存每個 item 最相似的兩百個鄰居。模型選擇和測試完全分開。相同 pipeline 也已經在十萬到一百萬使用者的四個規模跑完。錄影時可在 workbook 或 repository 快速指出這幾個檔案。

## 10. 超參數

時間：9:20–10:25（65 秒）

這張圖是 validation ablation。橫軸 alpha 是 BPR 權重；alpha 等於一就是只有 BPR，所以右端分數大幅下降。混合在 0.75 最高，而 popularity penalty lambda 沒有改善 NDCG，因此最後選零。ItemKNN 選兩百個鄰居；BPR 在 32/64 factors、兩種 regularization、10/20 epochs 中選出 64 factors、20 epochs。所有決定都沒有使用 test。

## 11. 評估指標

時間：10:25–11:35（70 秒）

Recall 看十個位置找回多少答案；NDCG 還會讓排得前面的命中得到更高權重，因此是主要選參數指標。Coverage 則完全不同，它問模型推薦過多少不同頻道，所以高 coverage 不代表高 accuracy。Hit rate、novelty、long-tail exposure 和 candidate coverage 用來補足產品觀點。這裡的核心是，不能只用一個分數宣稱模型全面最好。

## 12. 主要結果

時間：11:35–13:10（95 秒）

Hybrid 的 Recall 是 0.2234，NDCG 是 0.1315，兩者都是最高。ItemKNN NDCG 0.1258，是最強單一模型。BPR 只有 0.0542，但仍比 popularity 高。Hybrid 相對近期熱門度提升約百分之二百四十八，證明個人化歷史有預測力。不過 Hybrid 的 catalog coverage 只有百分之二十六，ItemKNN 是百分之三十七，所以 Hybrid 是準確度最佳，不是所有產品目標都最佳。Count-weighted ItemKNN 的準確度更低，但多樣性最高，也說明不同目標會選不同模型。

## 13. BPR 與 Hybrid 解釋

時間：13:10–14:50（100 秒）

BPR 較弱不是單一 bug。第一，長尾 item 的 embedding 資料不足。第二，直播未觀看可能只代表當時沒開播。第三，每個 positive 只抽一個 uniform negative，通常是非常容易的負例，無法教模型區分相似候選。第四，低維 latent space 不一定能保留 ItemKNN 的局部關係。五個不同 seeds 的 BPR 仍然遠低於 ItemKNN，所以不是 seed 258 特別倒楣。可是 BPR 單獨命中五千多個 ItemKNN 沒命中的 positive，因此融合後仍有小幅、但 bootstrap 顯著的提升。

## 14. 群體差異

時間：14:50–16:05（75 秒）

模型對不同人和 item 的表現差很多。最冷門四分位的 target recall 只有 0.033，最熱門四分位超過 0.40，表示目前結果主要由較熱門的新頻道驅動。使用者歷史越長，NDCG 反而越低；可能是容易的相似頻道已經被看過，剩下的 unseen candidates 更難。真正零歷史使用者無法個人化，只能退回 popularity，NDCG 約 0.053。這些群體結果比單一平均數更能說明產品風險。

## 15. 穩健性與擴展

時間：16:05–17:20（75 秒）

Rolling-origin 的 early、middle、late 三個時間窗都保持 Hybrid、ItemKNN、BPR、Popularity 的排序，雖然越晚的絕對準確度下降。Scaling 實驗也用同一 seed、相同 hyperparameter grid、validation 兩千與 test 五千上限，完成十萬、二十萬、五十萬與一百萬使用者。Hybrid 和 ItemKNN 大致穩定，BPR 在 item catalog 擴張後下降。但 cohorts 和 catalogs 不固定，因此這只能支持 scalability 和 robustness，不是純粹 training-size 的因果 learning curve。

## 16. 相關文獻與限制

時間：17:20–18:45（85 秒）

原始 LiveRec 使用同一資料來源，但目標不同。它強調當下可觀看的 live content 和 repeat behavior；我們研究新頻道 discovery，並沒有精確 live status。因此兩邊數值不能直接比較，但 LiveRec 指出 availability 是下一步最重要的特徵。BPR 提供 pairwise ranking 基礎，LightGCN 則是可嘗試的圖協同過濾。未來除了更強模型，更重要的是改善 negative sampling、加入即時可用性與內容 metadata，並用線上 A/B test 驗證觀看時間和創作者曝光。

## 17. 結論

時間：18:45–20:00（75 秒）

最後有三個結論。第一，個人化明顯有效，Hybrid 遠高於熱門度。第二，在這個高度稀疏、只有互動資料的新頻道任務中，ItemKNN 的局部 co-view inductive bias 比目前 BPR 更合適。第三，最佳模型取決於目標：Hybrid 最準，但 ItemKNN 推薦更廣，冷啟動和即時 availability 仍然是上限。最重要的 takeaway 是，更多資料或更複雜模型不會自動更好；模型假設必須和資料及 target definition 一致。謝謝。
