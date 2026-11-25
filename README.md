# NKUST_news

國立高雄科技大學秘書室公共關係中心的新聞工具，包含兩個部分：

| 功能 | 檔案 | 說明 |
|---|---|---|
| 媒體露出彙編網頁 | `index.html` | 整理記者回報的報導連結，產出給長官的「新聞輿情彙編」 |
| 每日新聞信 | `main.py`、`.github/workflows/schedule.yml` | 每天 08:40 搜尋高科大相關新聞並寄出 Email |

---

## 一、媒體露出彙編網頁

網址：<https://szu10.github.io/NKUST_news/>

### 使用方式

1. **STEP 1**：填新聞稿標題、彙編日期，並貼上新聞稿全文。標題被記者大幅改寫時，系統會比對全文。
2. **STEP 2**：把 LINE 群組裡記者回報的訊息整段複製貼上，按「辨識連結」。
3. **STEP 2+**（選用）：按「搜尋網路露出」，自動搜尋網路上的相關報導，勾選後加入彙編。
4. **STEP 3**：確認辨識結果。需要時可修改媒體、標題、記者姓名，或排除無關的連結。
5. **產出**：
   - **LINE 貼文**：按「複製貼文」，貼到 LINE 群組。
   - **Google 試算表**：填好校內發稿日期、編號，按「複製表格內容」，在試算表點一格後貼上。

### 功能說明

- 自動辨識媒體與轉載平台（例如【波新聞/蕃新聞】），並依公關中心的媒體排序排列。
- 用自然語言比對標題與新聞稿全文，判斷報導是否為同一則新聞；無關的連結會自動排除，可手動復原。
- 略過 Google 雲端、LINE 邀請、Facebook 等非新聞連結。
- 媒體排序與網域可在頁面最下方「媒體排序與網域設定」調整，但設定只存在各自的瀏覽器。要改全體預設，請修改 `index.html` 裡的 `DEFAULT_MAIN`、`DEFAULT_AGG`。
- 資料只存在使用者自己的瀏覽器，不會上傳。

### 網路搜尋服務（Google Apps Script）

「搜尋網路露出」按鈕需要搭配 Google Apps Script 搜尋服務。GitHub Pages 只能放靜態網頁，無法讀取其他新聞網站，所以由 Apps Script 代為搜尋 Google News、讀取報導內文、還原短網址。

**設定方式**

1. 到 <https://script.google.com> 建立新專案，貼上 `Code.gs` 的內容並儲存。
2. 選 `testSearch` 函式按「執行」，完成授權。
3. 「部署」→「新增部署作業」→「網頁應用程式」：
   - 執行身分：我
   - 誰可以存取：所有人
4. 複製結尾為 `/exec` 的網址，填入 `index.html` 的 `DEFAULT_ENDPOINT`，或在網頁的「媒體排序與網域設定」中填入。目前已設定為公關中心部署的網址。

修改 `Code.gs` 後，要到「部署」→「管理部署作業」→ 編輯 → 版本選「新版本」→「部署」，修改才會生效，網址不變。

### 更新網頁

在 repo 首頁按 **Add file → Upload files**，上傳新的 `index.html` 覆蓋舊檔，約 1–2 分鐘生效。

---

## 二、每日新聞信

- 每天台灣時間 08:40，由 GitHub Actions 執行 `main.py`。
- 從 Google News RSS 搜尋「國立高雄科技大學」「高科大」「NKUST」「高雄科大」「高雄科技大學」的前一天到當天新聞，寄送「NKUST新聞日報」。
- 需要在 **Settings → Secrets and variables → Actions** 設定以下三個值：
  - `SENDER_EMAIL`：寄件 Gmail
  - `APP_PASSWORD`：Google 應用程式密碼（不是一般登入密碼）
  - `RECEIVER_EMAIL`：收件信箱
- 手動測試：**Actions → Daily NKUST News Bot → Run workflow**。
