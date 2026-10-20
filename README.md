# 學測英文單字練習

整理自 106–115 學年度學測與指考英文試題的高頻單字與片語練習網站。純 HTML 網頁，不依賴任何外部套件，放上 GitHub Pages 即可使用。

## 檔案結構

```
index.html             首頁（連到三份題庫）
vocab-quiz.html        測驗主程式
data/
  A.json               A 級必背 244 字
  B.json               B 級重要 1032 字
  P.json               高頻片語 130 個
tools/
  csv-to-json.html     Excel 母檔轉 JSON 工具
.nojekyll              讓 GitHub Pages 直接提供檔案，不經 Jekyll 處理
```

## 上傳到 GitHub Pages

1. 在 GitHub 建立一個新的儲存庫（Repository），設為 Public。
2. 進入儲存庫，按「Add file」→「Upload files」，把本資料夾內的所有檔案和資料夾拖進去，按「Commit changes」。
3. 到「Settings」→「Pages」，在「Branch」選擇 `main`、資料夾選 `/ (root)`，按「Save」。
4. 等一兩分鐘後，頁面上方會出現網址，格式為 `https://帳號名稱.github.io/儲存庫名稱/`。

注意：`.nojekyll` 是隱藏檔，部分電腦的檔案總管預設看不到。如果上傳時漏掉也沒關係，網站仍可正常運作。

## 網址用法

- `index.html`：首頁
- `vocab-quiz.html?set=A`、`?set=B`、`?set=P`：直接開啟 A 級、B 級、片語題庫
- `vocab-quiz.html?set=demo`：內建的範例題庫

直接在電腦上雙擊開啟 HTML 時，瀏覽器的安全限制不允許讀取 `data/` 裡的檔案，只能用測驗頁的「上傳 JSON 題庫」測試。放上 GitHub Pages 後就沒有這個限制。

## 更新題庫

題庫的原始資料是 Excel 母檔（不放在網站上）：

1. 在母檔修改藍字欄（中文、誘答、易混字、補充說明、例句、例句中譯），黑字的解析、出處和檢查欄會自動更新。
2. 「檢查」欄若出現紅字，先修正再繼續。
3. 另存成「CSV UTF-8（逗號分隔）」。
4. 開啟 `tools/csv-to-json.html`，拖入 CSV，確認沒有警告後下載 JSON，檔名改成對應的 `A.json`、`B.json` 或 `P.json`。
5. 在 GitHub 上傳新檔，取代 `data/` 裡的舊檔。

## 題庫欄位

| 欄位 | 必填 | 說明 |
|---|---|---|
| word | 是 | 題目單字或片語，可用 `**粗體**` 標出重點字 |
| correctAnswer | 是 | 正確的中文意思 |
| options | 否 | 選項陣列，須包含正解；省略或不足 4 個時，自動從其他題目的中文補齊 |
| pos | 否 | 詞性或片語類別；自動補選項時會優先找同詞性 |
| level | 否 | 參考詞彙表級數 |
| explanation | 否 | 解析，可用 `**粗體**` 和換行 |
| example | 否 | 例句，可用 `**粗體**` 標出目標字 |
| exampleZh | 否 | 例句中譯，可用 `**粗體**` 標出目標字對應的中文 |
| source | 否 | 出處 |

## 錯題本

錯題本存在各自裝置的瀏覽器裡（localStorage），不會上傳到任何地方。換手機、換瀏覽器或清除瀏覽資料後會重新開始，可先用錯題本頁面的「匯出 JSON」備份。

## 資料來源

題目內容整理自大學入學考試中心公布之歷屆學測與指考英文試題，僅供學習使用。
