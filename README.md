# 通識課志願序與中選機率分析系統

## 專案簡介

本專案是一個以 Python 為主的選課輔助系統，主要目標是從中央大學課程系統的課程詳細頁中擷取課程資料與修課名單，並進一步分析每門課的報名人數、志願序分布與中選門檻，協助學生在選課時判斷課程競爭程度。

本專題的核心重點是「資料爬取與資料整理」，分析與視覺化則作為後續應用。系統會先批次下載課程 HTML，解析課程基本資訊與修課學生名單，再根據人數限制與志願序規則推估課程的中選難度，最後輸出 CSV 分析結果與 HTML 視覺化報表。

---

## 作品動機

在選課時，學生通常只能看到課程名稱、老師、時間與人數限制，但很難直接判斷一門課實際上有多熱門，也不容易知道自己應該把某門課填在第幾志願才比較有機會中選。

尤其在志願序選課制度下，單純知道「有多少人登記」並不夠，因為中選機會會受到下列因素影響：

1. 課程人數限制
2. 待分發人數
3. 不同學生填寫的志願序
4. 第幾志願開始超過課程容量
5. 門檻志願序的剩餘名額與中選率

因此，本專案希望透過爬蟲與資料分析，將原本分散在課程網頁中的資訊整理成更容易閱讀的表格與報表，讓學生可以更直覺地理解課程競爭情況。

---

## 主要功能

### 1. 批次爬取課程詳細頁

系統會根據課程代碼 `crs_id` 批次下載課程詳細頁 HTML，並儲存在 `raw/` 資料夾中。

目前預設抓取範圍為：

```python
crs_ids = list(range(9001, 9062))
```

每一門課會儲存成：

```text
raw/course_<crs_id>.html
```

例如：

```text
raw/course_9044.html
```

程式也支援快取機制，若本機已經存在對應 HTML 檔案，預設會直接使用本機資料，避免重複發送請求。

---

### 2. 解析課程基本資料

系統會從課程頁面中解析以下課程資訊：

* 課程代碼
* 課程名稱
* 授課教師
* 開課系所
* 上課時間與地點
* 必修或選修
* 學分數
* 人數限制
* 待分發人數
* 中選人數

解析後會輸出成：

```text
output/courses.csv
```

---

### 3. 解析修課名單

系統會從 HTML 中尋找真正的修課名單表格，並解析每位學生的選課資料。

目前修課名單欄位包含：

* 課程代碼
* 序號
* 學號
* 姓名
* 系所
* 年級班別
* 性別
* 必修或選修
* 志願序
* 選課狀態

解析後會輸出成：

```text
output/course_students.csv
```

---

### 4. 資料來源可信度標記

由於網頁資料可能會出現欄位缺失或格式異常，本系統在課程基本資料中加入來源狀態標記。

目前使用的資料來源狀態包含：

```text
official
fallback_student_count
missing
unknown
```

說明如下：

| 狀態                     | 意義                    |
| ---------------------- | --------------------- |
| official               | 從官方課程資訊欄位成功取得         |
| fallback_student_count | 官方待分發人數缺失時，改用修課名單筆數推估 |
| missing                | 官方欄位缺失，且無法補值          |
| unknown                | 官方欄位有內容，但格式無法安全解析     |

此外，系統也會檢查官方待分發人數是否與修課名單筆數一致，並輸出檢查狀態。

---

### 5. 志願序門檻分析

系統會根據每門課的修課名單與人數限制，統計不同志願序的人數，並推估：

* 第 1 志願人數
* 中選門檻志願序
* 門檻志願序人數
* 門檻志願序前已占用名額
* 門檻志願序剩餘名額
* 門檻志願序中選率
* 建議填寫志願序
* 分析狀態
* 資料品質提醒

分析結果會輸出成：

```text
analysis/course_priority_analysis.csv
```

系統判斷邏輯大致如下：

如果某門課人數限制為 50 人，而第 1 志願已有 60 人登記，則中選門檻會落在第 1 志願，且第 1 志願的中選率約為：

```text
50 / 60 = 83.3%
```

如果第 1 志願人數尚未額滿，系統會繼續累加第 2 志願、第 3 志願，直到累積人數超過課程容量，藉此找出中選門檻志願序。

---

### 6. HTML 視覺化報表

系統會將分析結果整理成 HTML 報表，方便直接用瀏覽器查看。

輸出檔案為：

```text
analysis/result_view.html
```

目前報表包含四個分頁：

1. 最難中選課程前 10 名
2. 志願序門檻分析
3. 課表顯示
4. 課表明細

其中「最難中選課程前 10 名」會依照門檻志願序中選率由低到高排序。中選率越低，代表該課程競爭越激烈。

中選率以橫向長條圖呈現，顏色代表競爭程度：

| 中選率        | 顏色 | 意義    |
| ---------- | -- | ----- |
| 0% ~ 25%   | 紅色 | 非常競爭  |
| 26% ~ 50%  | 橙色 | 競爭偏高  |
| 51% ~ 75%  | 黃色 | 中等競爭  |
| 76% ~ 100% | 綠色 | 較容易中選 |

---

### 7. 課表顯示

系統會解析原始課程資料中的 `time_room` 欄位，將上課時間與教室拆解為：

* 星期
* 節次
* 時間
* 教室

並輸出課表明細：

```text
analysis/course_schedule_entries.csv
```

同時在 HTML 報表中以課表格子的方式呈現課程時段，方便使用者查看不同課程是否有時間衝突。

---

## 專案檔案說明

```text
.
├── multi_files.py
├── analyze_priority.py
├── view_results.py
├── analyze_course.py
├── raw/
├── output/
└── analysis/
```

### multi_files.py

負責批次下載課程 HTML、解析課程基本資料、解析修課名單，並輸出原始整理後的 CSV 檔案。

主要輸出：

```text
output/courses.csv
output/course_students.csv
output/failed_courses.txt
```

---

### analyze_priority.py

負責根據課程資料與修課名單進行志願序門檻分析。

主要輸出：

```text
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
```

---

### view_results.py

負責讀取分析結果並產生 HTML 視覺化報表。

主要輸出：

```text
analysis/result_view.html
analysis/course_schedule_entries.csv
```

---

### analyze_course.py

早期版本的熱門度分析程式，主要根據待分發人數與人數限制計算熱門度倍率與超額人數。

目前主要分析流程已改由 `analyze_priority.py` 負責，因為志願序門檻與中選率比單純熱門度倍率更符合使用者需求。

---

## 安裝套件

本專案使用 Python 撰寫，建議使用 Python 3.10 以上版本。

需要安裝的套件如下：

```bash
pip install requests beautifulsoup4 pandas urllib3
```

---

## 執行方式

### 第一步：爬取並解析課程資料

```bash
python multi_files.py
```

執行後會產生：

```text
raw/course_<crs_id>.html
output/courses.csv
output/course_students.csv
output/failed_courses.txt
```

其中：

* `raw/`：儲存原始 HTML
* `output/courses.csv`：課程基本資料
* `output/course_students.csv`：修課名單
* `output/failed_courses.txt`：抓取或解析失敗的課程清單

---

### 第二步：進行志願序門檻分析

```bash
python analyze_priority.py
```

執行後會產生：

```text
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
```

其中：

* `course_priority_analysis.csv`：每門課的志願序門檻分析
* `student_estimated_accept_rate.csv`：每位學生依照志願序推估的中選率資料

---

### 第三步：產生 HTML 視覺化報表

```bash
python view_results.py
```

執行後會產生：

```text
analysis/result_view.html
analysis/course_schedule_entries.csv
```

程式會自動用瀏覽器開啟：

```text
analysis/result_view.html
```

---

## 建議執行順序

完整流程建議依照以下順序執行：

```bash
python multi_files.py
python analyze_priority.py
python view_results.py
```

如果想要重新抓取與分析資料，可以刪除以下資料夾後重新執行：

```text
raw/
output/
analysis/
```

若只想重新分析，不重新爬取資料，可以保留 `raw/` 與 `output/`，只刪除 `analysis/` 後重新執行：

```bash
python analyze_priority.py
python view_results.py
```

---

## 目前完成狀態

目前已完成：

* 批次下載課程詳細頁 HTML
* 本機 HTML 快取機制
* 課程基本資料解析
* 修課名單 table 定位與解析
* 多門課程整合輸出 CSV
* 失敗課程紀錄
* 人數欄位資料來源可信度標記
* 官方待分發人數與修課名單筆數一致性檢查
* 待分發人數 fallback 機制
* 志願序分布統計
* 中選門檻志願序推估
* 門檻志願序中選率計算
* 系統建議文字產生
* 課表時間與教室解析
* HTML 視覺化報表
* 搜尋功能
* 最難中選課程前 10 名
* 志願序門檻分析表
* 課表顯示
* 課表明細

---

## 目前限制

1. 目前課程代碼範圍需要在程式中手動設定。
2. 系統依賴中央大學課程詳細頁的 HTML 結構，若網站欄位名稱或表格格式改變，解析規則需要同步調整。
3. 中選率是根據目前待分發名單與志願序規則推估，並不代表最終正式分發結果。
4. 若課程人數限制缺失或格式異常，該課程無法進行完整中選率分析。
5. 目前 HTML 報表以本機靜態檔案為主，尚未做成完整網站或互動式前端系統。
6. 目前未加入使用者個人課程偏好推薦，例如依照系所、興趣、時間空堂自動推薦課程。

---

## 後續可改進方向

未來可以加入以下功能：

1. 將課程代碼範圍改成設定檔或命令列參數
2. 加入更完整的錯誤處理與 log 紀錄
3. 支援不同學期資料比較
4. 加入課程關鍵字搜尋與篩選
5. 加入使用者個人空堂檢查
6. 加入課程推薦排序
7. 將 HTML 報表改成 Web App
8. 將分析結果轉成互動式圖表
9. 加入資料更新時間與版本紀錄
10. 強化 HTML 結構變動時的解析穩定性

---

## 專案成果

本專案目前已完成從資料爬取、資料清理、資料可信度標記、志願序分析到 HTML 視覺化報表的完整流程。

整體流程如下：

```text
課程詳細頁 HTML
        ↓
multi_files.py
        ↓
output/courses.csv
output/course_students.csv
        ↓
analyze_priority.py
        ↓
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
        ↓
view_results.py
        ↓
analysis/result_view.html
```

本系統可以協助學生快速了解不同課程的競爭程度，並以志願序門檻與中選率作為選課決策參考。
