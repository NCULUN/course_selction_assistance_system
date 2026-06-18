
````markdown
# 通識課熱門度與中選機率分析系統

本專案是一個以 Python 實作的選課輔助分析系統，主要針對中央大學課程詳細頁進行資料爬取、整理與分析，協助學生理解課程熱門程度、志願序競爭情況，以及不同課程的中選門檻。

專題核心以「課程資料爬蟲」為主，並延伸加入資料分析與 HTML 視覺化報表，讓使用者可以更直觀地查看熱門課程、志願序門檻與課表資訊。

---

## 專案功能

### 1. 課程資料爬取

系統會根據課程代碼批次下載課程詳細頁 HTML，並解析出以下資料：

- 課程代號
- 課程名稱
- 授課教師
- 開課系所
- 上課時間與教室
- 必選修
- 學分數
- 人數限制
- 待分發人數
- 已中選人數
- 修課名單
- 學生志願序
- 選課狀態

下載後的 HTML 會存放在 `raw/` 資料夾中，解析後的 CSV 會輸出到 `output/` 資料夾。

---

### 2. 熱門度分析

系統會根據課程的「待分發人數」與「人數限制」計算熱門度倍率。

熱門度倍率計算方式：

```text
熱門度倍率 = 待分發人數 / 人數限制
````

倍率越高，代表該課程越熱門、競爭程度越高。

同時也會計算超額人數：

```text
超額人數 = 待分發人數 - 人數限制
```

分析結果會輸出為：

```text
analysis/popular_courses.csv
```

---

### 3. 志願序門檻分析

本專案根據學校選課規則進行推估：

志願序越前面的學生越有優先選擇權。

例如：

若課程人數上限為 50 人，但第 1 志願就有 60 人登記，則系統會推估該課程的中選門檻落在第 1 志願，且第 1 志願內仍需競爭。

系統會分析每門課的志願序分布，推估以下資訊：

* 第 1 志願人數
* 中選門檻志願序
* 門檻志願序人數
* 門檻志願序剩餘名額
* 門檻志願序預估中選率
* 建議填在第幾志願以內較有機會

分析結果會輸出為：

```text
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
```

其中 `course_priority_analysis.csv` 是主要成果檔案。

---

### 4. 課表顯示與 HTML 報表

系統會將原本較難閱讀的 `time_room` 欄位拆解成：

* 星期
* 節次
* 時間
* 教室

並產生整合式 HTML 成果頁面，包含以下內容：

* 熱門課程前 10 名
* 志願序門檻分析
* 課表顯示
* 課表明細搜尋

輸出檔案為：

```text
analysis/result_view.html
analysis/course_schedule_entries.csv
```

使用者可以直接開啟 `analysis/result_view.html` 查看分析結果。

---

## 專案架構

```text
course-selection-helper/
│
├── multi_files.py
├── analyze_course.py
├── analyze_priority.py
├── view_results.py
│
├── raw/
│   ├── course_9001.html
│   ├── course_9002.html
│   └── ...
│
├── output/
│   ├── courses.csv
│   ├── course_students.csv
│   └── failed_courses.txt
│
├── analysis/
│   ├── popular_courses.csv
│   ├── course_priority_analysis.csv
│   ├── student_estimated_accept_rate.csv
│   ├── course_schedule_entries.csv
│   └── result_view.html
│
└── README.md
```

---

## 檔案說明

### multi_files.py

負責批次爬取與解析課程資料。

主要功能：

* 依照課程代碼下載課程詳細頁 HTML
* 將 HTML 儲存至 `raw/`
* 解析課程基本資料
* 解析修課名單 table
* 匯出課程總表 `output/courses.csv`
* 匯出修課名單總表 `output/course_students.csv`
* 記錄無法成功解析的課程至 `output/failed_courses.txt`

程式中預設爬取範圍：

```python
crs_ids = list(range(9001, 9062))
```

如果要改成其他課程範圍，可以直接修改這一行。

---

### analyze_course.py

負責基本熱門度分析。

輸入：

```text
output/courses.csv
output/course_students.csv
```

輸出：

```text
analysis/popular_courses.csv
```

分析內容：

* 熱門度倍率
* 超額人數
* 熱門課程排序

---

### analyze_priority.py

負責志願序門檻分析，是本專案的主要分析核心。

輸入：

```text
output/courses.csv
output/course_students.csv
```

輸出：

```text
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
```

分析內容：

* 各志願序人數統計
* 中選門檻志願序
* 門檻志願序剩餘名額
* 門檻志願序中選率
* 系統建議

---

### view_results.py

負責產生 HTML 視覺化結果頁。

輸入：

```text
output/courses.csv
output/course_students.csv
analysis/course_priority_analysis.csv
```

輸出：

```text
analysis/result_view.html
analysis/course_schedule_entries.csv
```

HTML 頁面包含：

* 熱門課程前 10 名
* 志願序門檻分析表
* 課表格狀顯示
* 課表明細表
* 搜尋功能

---

## 環境需求

建議使用 Python 3.10 以上版本。

需要安裝的套件：

```bash
pip install pandas requests beautifulsoup4 urllib3
```

---

## 執行方式

請依照以下順序執行。

### 1. 批次下載與解析課程資料

```bash
python multi_files.py
```

執行後會產生：

```text
raw/
output/courses.csv
output/course_students.csv
output/failed_courses.txt
```

如果 `raw/` 中已經有下載過的 HTML，程式會優先使用本機快取，避免重複下載。

---

### 2. 執行熱門度分析

```bash
python analyze_course.py
```

執行後會產生：

```text
analysis/popular_courses.csv
```

---

### 3. 執行志願序門檻分析

```bash
python analyze_priority.py
```

執行後會產生：

```text
analysis/course_priority_analysis.csv
analysis/student_estimated_accept_rate.csv
```

---

### 4. 產生 HTML 視覺化成果頁

```bash
python view_results.py
```

執行後會產生：

```text
analysis/result_view.html
analysis/course_schedule_entries.csv
```

程式會自動嘗試用瀏覽器開啟 `result_view.html`。

如果沒有自動開啟，也可以手動開啟：

```text
analysis/result_view.html
```

---

## 輸入與輸出資料說明

### output/courses.csv

課程基本資料總表。

主要欄位包含：

| 欄位名稱                      | 說明        |
| ------------------------- | --------- |
| course_id                 | 課程代號      |
| serial_number_course_code | 流水號 / 課程碼 |
| course_name               | 課程名稱      |
| instructor                | 授課教師      |
| department                | 開課系所      |
| educational_system        | 學制        |
| time_room                 | 上課時間與教室   |
| required_or_elective      | 必修或選修     |
| credit                    | 學分數       |
| semester_type             | 全年或學期     |
| lecture_language          | 授課語言      |
| code_card                 | 是否需要授權碼   |
| maximum_number            | 人數限制      |
| number_of_assigned        | 待分發人數     |
| number_of_selected        | 已中選人數     |

---

### output/course_students.csv

修課名單總表。

主要欄位包含：

| 欄位名稱                 | 說明    |
| -------------------- | ----- |
| course_id            | 課程代號  |
| no                   | 序號    |
| student_id           | 學號    |
| name                 | 姓名    |
| department           | 學生系所  |
| class_name           | 年級班別  |
| gender               | 性別    |
| required_or_elective | 必修或選修 |
| priority             | 志願序   |
| status               | 選課狀態  |

---

### analysis/popular_courses.csv

熱門度分析結果。

主要欄位包含：

| 欄位名稱               | 說明    |
| ------------------ | ----- |
| course_id          | 課程代號  |
| course_name        | 課程名稱  |
| instructor         | 授課教師  |
| maximum_number     | 人數限制  |
| number_of_assigned | 待分發人數 |
| number_of_selected | 已中選人數 |
| popularity_ratio   | 熱門度倍率 |
| over_capacity      | 超額人數  |

---

### analysis/course_priority_analysis.csv

志願序門檻分析結果。

主要欄位包含：

| 欄位名稱                      | 說明          |
| ------------------------- | ----------- |
| course_id                 | 課程代號        |
| course_name               | 課程名稱        |
| instructor                | 授課教師        |
| time_room                 | 原始上課時間與教室   |
| maximum_number            | 人數限制        |
| number_of_assigned        | 待分發人數       |
| popularity_ratio          | 熱門度倍率       |
| over_capacity             | 超額人數        |
| priority_1_count          | 第 1 志願人數    |
| cutoff_priority           | 中選門檻志願序     |
| cutoff_priority_count     | 門檻志願序人數     |
| seats_before_cutoff       | 門檻前已佔名額     |
| seats_remaining_at_cutoff | 門檻志願序剩餘名額   |
| cutoff_accept_rate        | 門檻志願序預估中選率  |
| recommended_max_priority  | 建議最高志願序     |
| no_chance_after_priority  | 超過此志願序後機會較低 |
| recommendation            | 系統建議        |

---

### `analysis/course_schedule_entries.csv`

課表拆解後的明細資料。

主要欄位包含：

| 欄位名稱               | 說明       |
| ------------------ | -------- |
| course_id          | 課程代號     |
| course_name        | 課程名稱     |
| instructor         | 授課教師     |
| weekday            | 英文星期     |
| weekday_zh         | 中文星期     |
| period             | 節次       |
| time               | 上課時間     |
| room               | 教室       |
| maximum_number     | 人數限制     |
| number_of_assigned | 待分發人數    |
| popularity_ratio   | 熱門度倍率    |
| cutoff_priority    | 中選門檻志願序  |
| cutoff_accept_rate | 門檻志願序中選率 |
| recommendation     | 系統建議     |

---

## 分析方法說明

### 熱門度倍率

```text
popularity_ratio = number_of_assigned / maximum_number
```

例如：

```text
人數限制 = 50
待分發人數 = 150
熱門度倍率 = 150 / 50 = 3.0
```

代表該課程登記人數為容量的 3 倍。

---

### 超額人數

```text
over_capacity = number_of_assigned - maximum_number
```

例如：

```text
人數限制 = 50
待分發人數 = 80
超額人數 = 80 - 50 = 30
```

代表該課程多出 30 人競爭名額。

---

### 志願序門檻

系統會先統計每門課各志願序的人數，再依志願序由小到大累加。

例如：

| 志願序 | 人數 | 累積人數 |
| --- | -: | ---: |
| 1   | 30 |   30 |
| 2   | 15 |   45 |
| 3   | 20 |   65 |

若課程容量為 50 人，則：

* 第 1 志願一定有機會
* 第 2 志願仍在容量內
* 第 3 志願開始超過容量
* 因此中選門檻志願序為第 3 志願

第 3 志願的剩餘名額為：

```text
50 - 45 = 5
```

第 3 志願有 20 人競爭 5 個名額，所以門檻志願序中選率為：

```text
5 / 20 = 0.25 = 25%
```

---

## 使用範例

假設系統分析後產生以下結果：

```text
課程名稱：某熱門通識課
人數限制：50
待分發人數：120
熱門度倍率：2.4
第 1 志願人數：60
中選門檻志願序：1
門檻志願序中選率：83.3%
系統建議：建議填在第 1 志願以內才有機會
```

代表該課程非常熱門，且第 1 志願人數已經超過或接近課程容量，因此若學生將該課程放在較後面的志願序，中選機會會明顯降低。

---

## 注意事項

本專案的分析結果是根據目前爬取到的課程資料與修課名單進行推估，並不代表學校正式分發結果。

實際選課結果仍可能受到以下因素影響：

* 學校選課系統的完整分發規則
* 加退選階段變動
* 擋修條件
* 年級或系所限制
* 授權碼
* 課程人數調整
* 特殊身分或特殊規則

因此，本系統適合作為選課前的參考工具，而不是保證中選的判斷依據。

---

## 資料隱私提醒

本專案可能會處理修課名單資料，其中可能包含學號、姓名、系所等資訊。

如果 GitHub repository 是公開的，建議：

* 不要上傳未遮蔽的學生個資
* 不要上傳完整修課名單
* 可改用匿名化後的範例資料
* 或將 `raw/`、`output/course_students.csv` 加入 `.gitignore`

建議 `.gitignore` 可加入：

```text
__pycache__/
*.pyc

raw/
output/course_students.csv
analysis/student_estimated_accept_rate.csv
```

如果課程資料與修課名單已經過匿名化處理，則可以視需求保留範例資料供展示。

---

## 專題特色

* 使用 Python 自動化爬取課程資料
* 將 HTML 課程頁轉換為結構化 CSV
* 分析課程熱門度與超額情況
* 根據志願序規則推估中選門檻
* 將上課時間地點轉換成課表格式
* 產生可直接開啟的 HTML 視覺化報表
* 適合作為選課輔助工具與資料分析專題展示

---

## 未來可改進方向

* 加入更多學期資料，比較不同學期熱門度變化
* 加入教師、開課系所、年級分布等進階分析
* 將 HTML 報表改成互動式網頁系統
* 加入課程搜尋與篩選功能
* 加入課程推薦演算法
* 支援使用者自訂想選課程清單
* 根據個人志願序規劃推薦填課策略

---

## 專案執行流程總結

```text
multi_files.py
        ↓
output/courses.csv
output/course_students.csv
        ↓
analyze_course.py
        ↓
analysis/popular_courses.csv
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

---

## 作者
陳冠綸2026.06.18
本專案為選課輔助系統專題，使用 Python 完成資料爬取、清理、分析與視覺化。

```
```
