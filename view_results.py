import re
import html
import webbrowser
from pathlib import Path

import pandas as pd


WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

WEEKDAY_ZH = {
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日"
}


def escape(value):
    """
    避免 HTML 特殊字元造成顯示錯誤
    """
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def read_required_csv(path):
    """
    讀取必要 CSV，若不存在則給清楚錯誤
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"找不到檔案：{path}")

    return pd.read_csv(path)


def parse_time_room(time_room):
    """
    將 time_room 解析成：
    [
        {
            "weekday": "Wednesday",
            "weekday_zh": "星期三",
            "period": 3,
            "time": "10:00 - 10:50",
            "room": "General Education Building 122"
        },
        ...
    ]

    原始格式大概長這樣：
    Wednesday 3 (10:00 - 10:50) | General Education Building 122
    Wednesday 4 (11:00 - 11:50) | General Education Building 122
    """
    if pd.isna(time_room):
        return []

    text = str(time_room).strip()

    pattern = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(\d+)\s+"
        r"\((.*?)\)\s+\|\s+"
        r"(.*?)(?=\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d+\s+\(|$)"
    )

    results = []

    for match in pattern.finditer(text):
        weekday = match.group(1)
        period = int(match.group(2))
        time = match.group(3).strip()
        room = match.group(4).strip()

        results.append({
            "weekday": weekday,
            "weekday_zh": WEEKDAY_ZH.get(weekday, weekday),
            "period": period,
            "time": time,
            "room": room
        })

    return results


def build_schedule_entries(priority_analysis):
    """
    從 course_priority_analysis.csv 裡的 time_room
    拆成一列一個上課時段的資料。

    注意：time_room 只用來建立課表，不再放進熱門課程與志願序分析表。
    """
    entries = []

    for _, row in priority_analysis.iterrows():
        time_entries = parse_time_room(row.get("time_room", ""))

        for item in time_entries:
            entries.append({
                "course_id": row.get("course_id", ""),
                "course_name": row.get("course_name", ""),
                "instructor": row.get("instructor", ""),
                "weekday": item["weekday"],
                "weekday_zh": item["weekday_zh"],
                "period": item["period"],
                "time": item["time"],
                "room": item["room"],
                "maximum_number": row.get("maximum_number", ""),
                "number_of_assigned": row.get("number_of_assigned", ""),
                "cutoff_priority": row.get("cutoff_priority", ""),
                "cutoff_accept_rate": row.get("cutoff_accept_rate", ""),
                "recommendation": row.get("recommendation", "")
            })

    return pd.DataFrame(entries)

def format_percent(value):
    """
    將 0.833 轉成 83.3%
    """
    try:
        if pd.isna(value):
            return ""
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return ""


def format_accept_rate_bar(value):
    """
    將中選率顯示成橫向長條圖 + 百分比。

    顏色代表中選難度：
    0~25%：紅色，競爭最激烈
    26~50%：橙色
    51~75%：黃色
    76~100%：綠色，較容易中選
    """
    try:
        if pd.isna(value):
            return ""

        rate = float(value)
        rate = max(0.0, min(rate, 1.0))
        percent = rate * 100

        if percent <= 25:
            color_class = "rate-red"
        elif percent <= 50:
            color_class = "rate-orange"
        elif percent <= 75:
            color_class = "rate-yellow"
        else:
            color_class = "rate-green"

        return (
            "<div class='rate-cell'>"
            "<div class='rate-bar'>"
            f"<div class='rate-fill {color_class}' style='width: {percent:.1f}%;'></div>"
            "</div>"
            f"<span class='rate-label'>{percent:.1f}%</span>"
            "</div>"
        )
    except Exception:
        return ""


def format_ratio(value):
    """
    將熱門度倍率顯示成 x 倍
    """
    try:
        if pd.isna(value):
            return ""
        return f"{float(value):.2f} 倍"
    except Exception:
        return ""


def make_priority_display_table(priority_analysis):
    """
    製作適合顯示在 HTML 的志願序門檻分析表。

    已移除：熱門度倍率、超額人數、原始上課時間地點。
    排序與判斷改以「門檻志願序中選率」為核心。
    """
    df = priority_analysis.copy()

    df["門檻志願序中選率"] = df["cutoff_accept_rate"].apply(format_accept_rate_bar)

    display_cols = [
        "course_id",
        "course_name",
        "instructor",
        "maximum_number",
        "number_of_assigned",
        "priority_1_count",
        "cutoff_priority",
        "cutoff_priority_count",
        "seats_remaining_at_cutoff",
        "門檻志願序中選率",
        "recommendation"
    ]

    rename_map = {
        "course_id": "課程代號",
        "course_name": "課程名稱",
        "instructor": "授課教師",
        "maximum_number": "人數限制",
        "number_of_assigned": "待分發人數",
        "priority_1_count": "第 1 志願人數",
        "cutoff_priority": "中選門檻志願序",
        "cutoff_priority_count": "門檻志願序人數",
        "seats_remaining_at_cutoff": "門檻志願序剩餘名額",
        "recommendation": "系統建議"
    }

    existing_cols = [col for col in display_cols if col in df.columns]
    display_df = df[existing_cols].rename(columns=rename_map)

    # 因為中選率欄位要放 HTML 長條圖，所以表格輸出會使用 escape=False。
    # 其他文字欄位先在這裡做 HTML escape，避免課程名稱或教師名稱造成顯示錯誤。
    raw_html_cols = {"門檻志願序中選率"}
    for col in display_df.columns:
        if col not in raw_html_cols:
            display_df[col] = display_df[col].apply(escape)

    return display_df

def make_schedule_detail_table(schedule_entries):
    """
    製作課表明細表。

    課表明細保留星期、節次、時間、教室；不顯示熱門度倍率與超額人數。
    """
    if schedule_entries.empty:
        return pd.DataFrame()

    df = schedule_entries.copy()

    df["門檻志願序中選率"] = df["cutoff_accept_rate"].apply(format_accept_rate_bar)

    display_cols = [
        "course_id",
        "course_name",
        "instructor",
        "weekday_zh",
        "period",
        "time",
        "room",
        "maximum_number",
        "number_of_assigned",
        "cutoff_priority",
        "門檻志願序中選率",
        "recommendation"
    ]

    rename_map = {
        "course_id": "課程代號",
        "course_name": "課程名稱",
        "instructor": "授課教師",
        "weekday_zh": "星期",
        "period": "節次",
        "time": "時間",
        "room": "教室",
        "maximum_number": "人數限制",
        "number_of_assigned": "待分發人數",
        "cutoff_priority": "中選門檻志願序",
        "recommendation": "系統建議"
    }

    existing_cols = [col for col in display_cols if col in df.columns]
    display_df = df[existing_cols].rename(columns=rename_map)

    raw_html_cols = {"門檻志願序中選率"}
    for col in display_df.columns:
        if col not in raw_html_cols:
            display_df[col] = display_df[col].apply(escape)

    return display_df

def build_schedule_grid_html(schedule_entries):
    """
    將課程轉成課表格子。
    同一星期同一節如果有多門課，會全部列在同一格。
    """
    if schedule_entries.empty:
        return "<p>沒有可解析的課表資料。</p>"

    existing_weekdays = [
        day for day in WEEKDAY_ORDER
        if day in set(schedule_entries["weekday"])
    ]

    periods = sorted(schedule_entries["period"].dropna().astype(int).unique())

    html_parts = []

    html_parts.append('<div class="schedule-container">')
    html_parts.append('<table class="schedule-grid">')

    # 表頭
    html_parts.append("<thead>")
    html_parts.append("<tr>")
    html_parts.append("<th class='period-col'>節次</th>")

    for weekday in existing_weekdays:
        html_parts.append(f"<th>{WEEKDAY_ZH.get(weekday, weekday)}</th>")

    html_parts.append("</tr>")
    html_parts.append("</thead>")

    # 表身
    html_parts.append("<tbody>")

    for period in periods:
        html_parts.append("<tr>")
        html_parts.append(f"<th class='period-col'>第 {period} 節</th>")

        for weekday in existing_weekdays:
            cell_df = schedule_entries[
                (schedule_entries["weekday"] == weekday)
                & (schedule_entries["period"].astype(int) == period)
            ]

            html_parts.append("<td>")

            if cell_df.empty:
                html_parts.append("<div class='empty-cell'>—</div>")
            else:
                for _, row in cell_df.iterrows():
                    cutoff_rate = format_percent(row.get("cutoff_accept_rate", ""))

                    html_parts.append("<div class='course-card'>")
                    html_parts.append(
                        f"<div class='course-title'>"
                        f"{escape(row.get('course_id', ''))}｜{escape(row.get('course_name', ''))}"
                        f"</div>"
                    )
                    html_parts.append(
                        f"<div class='course-meta'>教師：{escape(row.get('instructor', ''))}</div>"
                    )
                    html_parts.append(
                        f"<div class='course-meta'>時間：{escape(row.get('time', ''))}</div>"
                    )
                    html_parts.append(
                        f"<div class='course-meta'>教室：{escape(row.get('room', ''))}</div>"
                    )
                    html_parts.append(
                        f"<div class='course-badges'>"
                        f"<span>門檻志願 {escape(row.get('cutoff_priority', ''))}</span>"
                        f"<span>門檻中選率 {escape(cutoff_rate)}</span>"
                        f"</div>"
                    )
                    html_parts.append("</div>")

            html_parts.append("</td>")

        html_parts.append("</tr>")

    html_parts.append("</tbody>")
    html_parts.append("</table>")
    html_parts.append("</div>")

    return "\n".join(html_parts)


def create_html_report(
    courses,
    students,
    priority_analysis,
    # student_estimated,
    schedule_entries
):
    """
    產生完整 HTML 報表
    """
    Path("analysis").mkdir(exist_ok=True)

    html_path = Path("analysis/result_view.html")

    # 排序：中選率低的排前面，代表越難中選、越需要優先注意
    sort_cols = [
        col for col in ["cutoff_accept_rate", "cutoff_priority"]
        if col in priority_analysis.columns
    ]

    if sort_cols:
        priority_analysis = priority_analysis.sort_values(
            sort_cols,
            ascending=[True] * len(sort_cols)
        )

    priority_display = make_priority_display_table(priority_analysis)
    # student_display = make_student_display_table(student_estimated)
    schedule_detail_display = make_schedule_detail_table(schedule_entries)

    schedule_grid_html = build_schedule_grid_html(schedule_entries)

    top_10 = priority_display.head(10)

    html_content = f"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>通識課志願序與中選機率分析系統</title>
    <style>
        body {{
            font-family: Arial, "Microsoft JhengHei", sans-serif;
            margin: 0;
            background-color: #f5f6fa;
            color: #222;
        }}

        header {{
            background: linear-gradient(135deg, #2f4057, #526d82);
            color: white;
            padding: 28px 36px;
        }}

        header h1 {{
            margin: 0 0 8px 0;
            font-size: 28px;
        }}

        header p {{
            margin: 0;
            opacity: 0.9;
            line-height: 1.6;
        }}

        main {{
            padding: 28px 36px 50px 36px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .summary-card {{
            background-color: white;
            padding: 18px;
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }}

        .summary-card .label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }}

        .summary-card .value {{
            font-size: 26px;
            font-weight: bold;
            color: #2f4057;
        }}

        .tabs {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 22px 0;
        }}

        .tab-button {{
            border: none;
            background-color: #dbe4ee;
            color: #2f4057;
            padding: 12px 18px;
            border-radius: 999px;
            cursor: pointer;
            font-size: 15px;
            font-weight: bold;
        }}

        .tab-button.active {{
            background-color: #2f4057;
            color: white;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .card {{
            background-color: white;
            padding: 22px;
            margin-bottom: 28px;
            border-radius: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        }}

        h2 {{
            margin-top: 0;
            color: #2f4057;
        }}

        .note {{
            background-color: #fff8df;
            border-left: 5px solid #e0aa20;
            padding: 12px 16px;
            border-radius: 8px;
            line-height: 1.7;
            margin-bottom: 18px;
        }}

        input {{
            width: 100%;
            padding: 11px 12px;
            margin-bottom: 14px;
            font-size: 15px;
            border: 1px solid #bbb;
            border-radius: 8px;
            box-sizing: border-box;
        }}

        .table-container {{
            max-height: 650px;
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 10px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            background-color: white;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background-color: #e9eef5;
            position: sticky;
            top: 0;
            z-index: 2;
        }}

        tr:nth-child(even) {{
            background-color: #fafafa;
        }}

        .schedule-container {{
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 12px;
            max-height: 760px;
        }}

        .schedule-grid {{
            min-width: 1100px;
            table-layout: fixed;
        }}

        .schedule-grid th {{
            text-align: center;
        }}

        .period-col {{
            width: 90px;
            text-align: center;
            background-color: #eef3f8;
            font-weight: bold;
        }}

        .schedule-grid td {{
            min-width: 210px;
            height: 120px;
            background-color: #ffffff;
        }}

        .empty-cell {{
            color: #aaa;
            text-align: center;
            margin-top: 36px;
        }}

        .course-card {{
            background-color: #f2f6fb;
            border: 1px solid #d8e3ee;
            border-radius: 10px;
            padding: 9px;
            margin-bottom: 8px;
        }}

        .course-title {{
            font-weight: bold;
            color: #203040;
            margin-bottom: 6px;
            line-height: 1.4;
        }}

        .course-meta {{
            color: #444;
            font-size: 13px;
            line-height: 1.5;
        }}

        .course-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 7px;
        }}

        .course-badges span {{
            background-color: white;
            border: 1px solid #ccd8e4;
            color: #2f4057;
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 12px;
        }}

        .rate-cell {{
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 150px;
        }}

        .rate-bar {{
            flex: 1;
            height: 14px;
            background-color: #edf0f3;
            border-radius: 999px;
            overflow: hidden;
            border: 1px solid #d7dde3;
        }}

        .rate-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        .rate-label {{
            min-width: 48px;
            font-weight: bold;
            text-align: right;
        }}

        .rate-red {{
            background-color: #d9534f;
        }}

        .rate-orange {{
            background-color: #f0ad4e;
        }}

        .rate-yellow {{
            background-color: #f7d154;
        }}

        .rate-green {{
            background-color: #5cb85c;
        }}

        .footer {{
            color: #666;
            font-size: 13px;
            line-height: 1.7;
            margin-top: 28px;
        }}
    </style>
</head>
<body>

<header>
    <h1>通識課志願序與中選機率分析系統</h1>
    <p>
        本頁整合課程基本資料、修課名單、志願序門檻、預估中選率與課表顯示。
    </p>
</header>

<main>

    <section class="summary-grid">
        <div class="summary-card">
            <div class="label">課程數量</div>
            <div class="value">{len(courses)}</div>
        </div>
        <div class="summary-card">
            <div class="label">修課名單筆數</div>
            <div class="value">{len(students)}</div>
        </div>
        <div class="summary-card">
            <div class="label">志願序分析課程數</div>
            <div class="value">{len(priority_analysis)}</div>
        </div>
        <div class="summary-card">
            <div class="label">課表時段筆數</div>
            <div class="value">{len(schedule_entries)}</div>
        </div>
    </section>

    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'tabTop')">最難中選課程前 10 名</button>
        <button class="tab-button" onclick="openTab(event, 'tabPriority')">志願序門檻分析</button>
        <button class="tab-button" onclick="openTab(event, 'tabSchedule')">課表顯示</button>
        <button class="tab-button" onclick="openTab(event, 'tabScheduleDetail')">課表明細</button>
    </div>

    <section id="tabTop" class="tab-content active">
        <div class="card">
            <h2>最難中選課程前 10 名</h2>
            <div class="note">
                本分頁依照門檻志願序中選率由低到高排序。中選率越低，代表該課程競爭越激烈。
                顏色由紅、橙、黃、綠表示中選率由低到高，方便快速判斷選課風險。
            </div>
            <div class="table-container">
                {top_10.to_html(index=False, table_id="topTable", escape=False)}
            </div>
        </div>
    </section>

    <section id="tabPriority" class="tab-content">
        <div class="card">
            <h2>志願序門檻分析</h2>
            <div class="note">
                這張表是本專題的核心優化結果。系統會依照各課程的志願序分布與人數限制，
                推估中選門檻志願序、門檻志願序剩餘名額，以及該門檻志願序的預估中選率。
            </div>
            <input type="text" id="prioritySearch" placeholder="搜尋課程代號、課程名稱、老師、建議..." onkeyup="searchTable('prioritySearch', 'priorityTable')">
            <div class="table-container">
                {priority_display.to_html(index=False, table_id="priorityTable", escape=False)}
            </div>
        </div>
    </section>

    <section id="tabSchedule" class="tab-content">
        <div class="card">
            <h2>課表顯示</h2>
            <div class="note">
                系統將原本不易閱讀的 time_room 欄位拆解成星期、節次、時間與教室，
                並以課表格子的方式呈現。若同一時段有多門課，會全部列在同一格中。
            </div>
            {schedule_grid_html}
        </div>
    </section>

    <section id="tabScheduleDetail" class="tab-content">
        <div class="card">
            <h2>課表明細</h2>
            <input type="text" id="scheduleSearch" placeholder="搜尋課程名稱、老師、星期、教室..." onkeyup="searchTable('scheduleSearch', 'scheduleDetailTable')">
            <div class="table-container">
                {schedule_detail_display.to_html(index=False, table_id="scheduleDetailTable", escape=False)}
            </div>
        </div>
    </section>

    <div class="footer">
        輸出檔案：analysis/result_view.html、analysis/course_schedule_entries.csv。
        本分析結果是根據目前待分發名單與志願序規則進行推估，非最終分發結果。
    </div>

</main>

<script>
function openTab(event, tabId) {{
    var contents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < contents.length; i++) {{
        contents[i].classList.remove("active");
    }}

    var buttons = document.getElementsByClassName("tab-button");
    for (var j = 0; j < buttons.length; j++) {{
        buttons[j].classList.remove("active");
    }}

    document.getElementById(tabId).classList.add("active");
    event.currentTarget.classList.add("active");
}}

function searchTable(inputId, tableId) {{
    var input = document.getElementById(inputId);
    var filter = input.value.toLowerCase();
    var table = document.getElementById(tableId);

    if (!table) {{
        return;
    }}

    var tr = table.getElementsByTagName("tr");

    for (var i = 1; i < tr.length; i++) {{
        var rowText = tr[i].innerText.toLowerCase();

        if (rowText.indexOf(filter) > -1) {{
            tr[i].style.display = "";
        }} else {{
            tr[i].style.display = "none";
        }}
    }}
}}
</script>

</body>
</html>
"""

    html_path.write_text(html_content, encoding="utf-8")

    return html_path


def main():
    courses = read_required_csv("output/courses.csv")
    students = read_required_csv("output/course_students.csv")
    priority_analysis = read_required_csv("analysis/course_priority_analysis.csv")
    # student_estimated = read_required_csv("analysis/student_estimated_accept_rate.csv")

    # 若 course_priority_analysis.csv 已經移除 time_room，
    # 這裡會從 courses.csv 補回，讓課表顯示仍可正常產生。
    if "time_room" not in priority_analysis.columns and "time_room" in courses.columns:
        priority_analysis = priority_analysis.merge(
            courses[["course_id", "time_room"]],
            on="course_id",
            how="left"
        )

    # 保險：確保數字欄位為數字
    numeric_cols = [
        "maximum_number",
        "number_of_assigned",
        "number_of_selected",
        "priority_1_count",
        "cutoff_priority",
        "cutoff_priority_count",
        "seats_remaining_at_cutoff",
        "cutoff_accept_rate"
    ]

    for col in numeric_cols:
        if col in priority_analysis.columns:
            priority_analysis[col] = pd.to_numeric(priority_analysis[col], errors="coerce")

    schedule_entries = build_schedule_entries(priority_analysis)

    Path("analysis").mkdir(exist_ok=True)

    schedule_entries.to_csv(
        "analysis/course_schedule_entries.csv",
        index=False,
        encoding="utf-8-sig"
    )

    html_path = create_html_report(
        courses=courses,
        students=students,
        priority_analysis=priority_analysis,
        # student_estimated=student_estimated,
        schedule_entries=schedule_entries
    )

    print(f"已產生整合成果頁面：{html_path}")
    print("已產生課表明細 CSV：analysis/course_schedule_entries.csv")

    webbrowser.open(html_path.resolve().as_uri())


if __name__ == "__main__":
    main()