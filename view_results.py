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
    拆成一列一個上課時段的資料
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
                "popularity_ratio": row.get("popularity_ratio", ""),
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
    製作適合顯示在 HTML 的志願序門檻分析表
    """
    df = priority_analysis.copy()

    df["熱門度倍率"] = df["popularity_ratio"].apply(format_ratio)
    df["門檻志願序中選率"] = df["cutoff_accept_rate"].apply(format_percent)

    display_cols = [
        "course_id",
        "course_name",
        "instructor",
        "maximum_number",
        "number_of_assigned",
        "熱門度倍率",
        "over_capacity",
        "priority_1_count",
        "cutoff_priority",
        "cutoff_priority_count",
        "seats_remaining_at_cutoff",
        "門檻志願序中選率",
        "recommendation",
        "time_room"
    ]

    rename_map = {
        "course_id": "課程代號",
        "course_name": "課程名稱",
        "instructor": "授課教師",
        "maximum_number": "人數限制",
        "number_of_assigned": "待分發人數",
        "over_capacity": "超額人數",
        "priority_1_count": "第 1 志願人數",
        "cutoff_priority": "中選門檻志願序",
        "cutoff_priority_count": "門檻志願序人數",
        "seats_remaining_at_cutoff": "門檻志願序剩餘名額",
        "recommendation": "系統建議",
        "time_room": "原始上課時間地點"
    }

    existing_cols = [col for col in display_cols if col in df.columns]

    return df[existing_cols].rename(columns=rename_map)



def make_schedule_detail_table(schedule_entries):
    """
    製作課表明細表
    """
    if schedule_entries.empty:
        return pd.DataFrame()

    df = schedule_entries.copy()

    df["熱門度倍率"] = df["popularity_ratio"].apply(format_ratio)
    df["門檻志願序中選率"] = df["cutoff_accept_rate"].apply(format_percent)

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
        "熱門度倍率",
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

    return df[display_cols].rename(columns=rename_map)


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
                    popularity = format_ratio(row.get("popularity_ratio", ""))
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
                        f"<span>熱門度 {escape(popularity)}</span>"
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

    # 排序：熱門度高的排前面
    priority_analysis = priority_analysis.sort_values(
        ["popularity_ratio", "cutoff_priority"],
        ascending=[False, True]
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
    <title>通識課熱門度與中選機率分析系統</title>
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
    <h1>通識課熱門度與中選機率分析系統</h1>
    <p>
        本頁整合課程基本資料、修課名單、熱門度倍率、志願序門檻、預估中選率與課表顯示。
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
        <button class="tab-button active" onclick="openTab(event, 'tabTop')">熱門課程前 10 名</button>
        <button class="tab-button" onclick="openTab(event, 'tabPriority')">志願序門檻分析</button>
        <button class="tab-button" onclick="openTab(event, 'tabSchedule')">課表顯示</button>
        <button class="tab-button" onclick="openTab(event, 'tabScheduleDetail')">課表明細</button>
    </div>

    <section id="tabTop" class="tab-content active">
        <div class="card">
            <h2>熱門課程前 10 名</h2>
            <div class="note">
                熱門度倍率 = 待分發人數 / 人數限制。倍率越高，代表該課程需求越高。
                志願序門檻則表示依照目前報名資料推估，填到第幾志願仍可能有機會中選。
            </div>
            <div class="table-container">
                {top_10.to_html(index=False, table_id="topTable")}
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
                {priority_display.to_html(index=False, table_id="priorityTable")}
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
                {schedule_detail_display.to_html(index=False, table_id="scheduleDetailTable")}
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

    # 保險：確保數字欄位為數字
    numeric_cols = [
        "maximum_number",
        "number_of_assigned",
        "number_of_selected",
        "popularity_ratio",
        "over_capacity",
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