import pandas as pd
from pathlib import Path
import webbrowser


def main():
    courses_path = Path("output/courses.csv")
    students_path = Path("output/course_students.csv")

    if not courses_path.exists():
        print("找不到 output/courses.csv")
        return

    if not students_path.exists():
        print("找不到 output/course_students.csv")
        return

    courses = pd.read_csv(courses_path)
    students = pd.read_csv(students_path)

    # 轉成數字
    courses["maximum_number"] = pd.to_numeric(courses["maximum_number"], errors="coerce")
    courses["number_of_assigned"] = pd.to_numeric(courses["number_of_assigned"], errors="coerce")
    courses["number_of_selected"] = pd.to_numeric(courses["number_of_selected"], errors="coerce")

    # 熱門度分析
    courses["popularity_ratio"] = courses["number_of_assigned"] / courses["maximum_number"]
    courses["over_capacity"] = courses["number_of_assigned"] - courses["maximum_number"]

    # 排序：熱門度由高到低
    courses = courses.sort_values("popularity_ratio", ascending=False)

    # 顯示欄位
    course_cols = [
        "course_id",
        "course_name",
        "instructor",
        "maximum_number",
        "number_of_assigned",
        "number_of_selected",
        "popularity_ratio",
        "over_capacity",
        "time_room"
    ]

    student_cols = [
        "course_id",
        "no",
        "student_id",
        "name",
        "department",
        "class_name",
        "gender",
        "priority",
        "status"
    ]

    Path("analysis").mkdir(exist_ok=True)

    html_path = Path("analysis/result_view.html")

    html = f"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>通識課熱門度分析結果</title>
    <style>
        body {{
            font-family: Arial, "Microsoft JhengHei", sans-serif;
            margin: 30px;
            background-color: #f7f7f7;
        }}

        h1, h2 {{
            color: #333;
        }}

        .card {{
            background-color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
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
            z-index: 1;
        }}

        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        .table-container {{
            max-height: 650px;
            overflow: auto;
            border: 1px solid #ddd;
        }}

        .summary {{
            font-size: 16px;
            line-height: 1.8;
        }}

        input {{
            width: 100%;
            padding: 10px;
            margin-bottom: 12px;
            font-size: 16px;
            border: 1px solid #bbb;
            border-radius: 8px;
        }}
    </style>
</head>
<body>

    <h1>通識課熱門度分析結果</h1>

    <div class="card summary">
        <h2>資料摘要</h2>
        <p>課程數量：{len(courses)}</p>
        <p>修課名單總筆數：{len(students)}</p>
        <p>熱門度公式：待分發人數 / 人數限制</p>
    </div>

    <div class="card">
        <h2>課程熱門度排名</h2>
        <input type="text" id="courseSearch" placeholder="搜尋課程名稱、老師、課號..." onkeyup="searchTable('courseSearch', 'courseTable')">
        <div class="table-container">
            {courses[course_cols].to_html(index=False, table_id="courseTable")}
        </div>
    </div>

    <div class="card">
        <h2>完整修課名單</h2>
        <input type="text" id="studentSearch" placeholder="搜尋課號、系所、年級、志願序..." onkeyup="searchTable('studentSearch', 'studentTable')">
        <div class="table-container">
            {students[student_cols].to_html(index=False, table_id="studentTable")}
        </div>
    </div>

<script>
function searchTable(inputId, tableId) {{
    var input = document.getElementById(inputId);
    var filter = input.value.toLowerCase();
    var table = document.getElementById(tableId);
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

    html_path.write_text(html, encoding="utf-8")

    print(f"已產生分析結果頁面：{html_path}")

    # 自動用瀏覽器開啟
    webbrowser.open(html_path.resolve().as_uri())


if __name__ == "__main__":
    main()