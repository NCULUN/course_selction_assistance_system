import pandas as pd
from pathlib import Path


SOURCE_STATUS_COLUMNS = [
    "maximum_number_source_status",
    "number_of_assigned_source_status",
    "number_of_selected_source_status",
]

DATA_QUALITY_COLUMNS = [
    "student_list_count",
    "number_of_assigned_check_status",
]

SOURCE_FALLBACK_STUDENT_COUNT = "fallback_student_count"
SOURCE_MISSING = "missing"
SOURCE_UNKNOWN = "unknown"

CHECK_MISMATCH = "mismatch"


def safe_get(row, col, default=""):
    """
    安全取得 DataFrame row 裡的欄位。
    若舊版 courses.csv 還沒有 source_status 欄位，也不會讓程式出錯。
    """
    if col in row.index:
        value = row.get(col, default)
        if pd.isna(value):
            return default
        return value
    return default


def to_number(value):
    """
    將欄位轉成數字；失敗時回傳 NaN。
    """
    return pd.to_numeric(value, errors="coerce")


def to_int_or_blank(value):
    """
    輸出 CSV 時使用。
    可轉整數就輸出 int；不可轉就留空白，避免把 NaN 顯示給使用者。
    """
    value = to_number(value)
    if pd.isna(value):
        return ""
    return int(value)


def build_data_warning(course, capacity, assigned):
    """
    根據 source_status 與資料檢查結果，產生給前端或報告看的提醒文字。
    official 不特別提醒；只有 fallback / missing / unknown / mismatch 才提醒。
    """
    warnings = []

    maximum_source = safe_get(course, "maximum_number_source_status")
    assigned_source = safe_get(course, "number_of_assigned_source_status")
    assigned_check = safe_get(course, "number_of_assigned_check_status")

    if maximum_source == SOURCE_MISSING:
        warnings.append("人數限制缺資料")
    elif maximum_source == SOURCE_UNKNOWN or pd.isna(capacity):
        warnings.append("人數限制格式不明")

    if assigned_source == SOURCE_FALLBACK_STUDENT_COUNT:
        warnings.append("待分發人數由修課名單推估")
    elif assigned_source == SOURCE_MISSING:
        warnings.append("待分發人數缺資料")
    elif assigned_source == SOURCE_UNKNOWN or pd.isna(assigned):
        warnings.append("待分發人數格式不明")

    if assigned_check == CHECK_MISMATCH:
        warnings.append("官方待分發人數與修課名單筆數不一致")

    return "；".join(warnings)


def build_base_result(course, course_students, capacity, assigned):
    """
    建立每門課都共用的輸出欄位。
    做法 A 的重點就在這裡：把 courses.csv 的來源可信度欄位一起帶到
    analysis/course_priority_analysis.csv。
    """
    result = {
        "course_id": safe_get(course, "course_id"),
        "course_name": safe_get(course, "course_name"),
        "instructor": safe_get(course, "instructor"),
        "time_room": safe_get(course, "time_room"),
        "maximum_number": to_int_or_blank(capacity),
        "number_of_assigned": to_int_or_blank(assigned),
        "number_of_selected": to_int_or_blank(safe_get(course, "number_of_selected")),
        "student_list_count": safe_get(
            course,
            "student_list_count",
            len(course_students)
        ),
        "number_of_assigned_check_status": safe_get(
            course,
            "number_of_assigned_check_status"
        ),
        "maximum_number_source_status": safe_get(
            course,
            "maximum_number_source_status"
        ),
        "number_of_assigned_source_status": safe_get(
            course,
            "number_of_assigned_source_status"
        ),
        "number_of_selected_source_status": safe_get(
            course,
            "number_of_selected_source_status"
        ),
        "data_warning": build_data_warning(course, capacity, assigned),
    }

    return result


def calculate_priority_analysis(courses, students):
    results = []

    for _, course in courses.iterrows():
        course_id = course["course_id"]

        capacity = to_number(course.get("maximum_number", ""))
        assigned = to_number(course.get("number_of_assigned", ""))

        course_students = students[students["course_id"] == course_id].copy()

        base_result = build_base_result(
            course=course,
            course_students=course_students,
            capacity=capacity,
            assigned=assigned
        )

        # 沒有人數限制時，不能計算熱門度與志願序門檻，但仍保留在分析 CSV，
        # 讓前端或報告可以看見這門課是因為資料品質問題而無法分析。
        if pd.isna(capacity) or capacity <= 0:
            base_result.update({
                "popularity_ratio": "",
                "over_capacity": "",
                "priority_1_count": "",
                "cutoff_priority": "",
                "cutoff_priority_count": "",
                "seats_before_cutoff": "",
                "seats_remaining_at_cutoff": "",
                "cutoff_accept_rate": "",
                "recommended_max_priority": "",
                "no_chance_after_priority": "",
                "analysis_status": "invalid_capacity",
                "recommendation": "人數限制缺失或格式不明，無法計算中選率"
            })
            results.append(base_result)
            continue

        course_students["priority"] = pd.to_numeric(
            course_students["priority"],
            errors="coerce"
        )

        course_students = course_students.dropna(subset=["priority"])
        course_students["priority"] = course_students["priority"].astype(int)

        priority_counts = (
            course_students
            .groupby("priority")
            .size()
            .sort_index()
        )

        cumulative = 0
        cutoff_priority = None
        seats_before_cutoff = 0
        cutoff_priority_count = 0
        seats_remaining_at_cutoff = 0
        cutoff_accept_rate = 1.0

        for priority, count in priority_counts.items():
            previous_cumulative = cumulative
            cumulative += count

            if cumulative >= capacity:
                cutoff_priority = priority
                seats_before_cutoff = previous_cumulative
                cutoff_priority_count = count
                seats_remaining_at_cutoff = int(capacity - previous_cumulative)

                if count > 0:
                    cutoff_accept_rate = seats_remaining_at_cutoff / count
                else:
                    cutoff_accept_rate = 0

                break

        # 如果所有報名人數都沒有超過容量
        if cutoff_priority is None:
            cutoff_priority = int(priority_counts.index.max()) if len(priority_counts) > 0 else None
            seats_before_cutoff = int(cumulative)
            cutoff_priority_count = 0
            seats_remaining_at_cutoff = int(capacity - cumulative)
            cutoff_accept_rate = 1.0

        priority_1_count = int(priority_counts.get(1, 0))

        # number_of_assigned 若不可用，才退回修課名單筆數。
        # 正常情況下，新的 multi_files.py 已經會在 courses.csv 標記 fallback 來源。
        assigned_for_analysis = assigned if not pd.isna(assigned) else len(course_students)

        popularity_ratio = assigned_for_analysis / capacity
        over_capacity = assigned_for_analysis - capacity

        if cutoff_priority is None:
            recommendation = "報名資料不足，無法判斷"
            no_chance_after_priority = ""
            analysis_status = "insufficient_priority_data"
        elif len(course_students) <= capacity:
            recommendation = "報名人數未超過容量，各志願序皆有機會"
            no_chance_after_priority = ""
            analysis_status = "analyzed"
        else:
            recommendation = f"建議填在第 {cutoff_priority} 志願以內才有機會"
            no_chance_after_priority = cutoff_priority
            analysis_status = "analyzed"

        base_result.update({
            "number_of_assigned": int(assigned_for_analysis),
            "popularity_ratio": round(popularity_ratio, 3),
            "over_capacity": int(over_capacity),
            "priority_1_count": priority_1_count,
            "cutoff_priority": cutoff_priority,
            "cutoff_priority_count": cutoff_priority_count,
            "seats_before_cutoff": seats_before_cutoff,
            "seats_remaining_at_cutoff": seats_remaining_at_cutoff,
            "cutoff_accept_rate": round(cutoff_accept_rate, 3),
            "recommended_max_priority": cutoff_priority,
            "no_chance_after_priority": no_chance_after_priority,
            "analysis_status": analysis_status,
            "recommendation": recommendation
        })

        results.append(base_result)

    return pd.DataFrame(results)


def add_student_estimated_accept_rate(students, priority_analysis):
    students = students.copy()

    students["priority"] = pd.to_numeric(students["priority"], errors="coerce")

    merged = students.merge(
        priority_analysis[
            [
                "course_id",
                "maximum_number",
                "cutoff_priority",
                "cutoff_accept_rate",
                "analysis_status",
                "data_warning"
            ]
        ],
        on="course_id",
        how="left"
    )

    def estimate(row):
        priority = row["priority"]
        cutoff = row["cutoff_priority"]
        cutoff_rate = row["cutoff_accept_rate"]
        analysis_status = row.get("analysis_status", "")

        if analysis_status != "analyzed":
            return None

        if pd.isna(priority) or pd.isna(cutoff):
            return None

        if priority < cutoff:
            return 1.0
        elif priority == cutoff:
            return cutoff_rate
        else:
            return 0.0

    merged["estimated_accept_rate"] = merged.apply(estimate, axis=1)

    return merged


def main():
    courses_path = Path("output/courses.csv")
    students_path = Path("output/course_students.csv")

    courses = pd.read_csv(courses_path)
    students = pd.read_csv(students_path)

    priority_analysis = calculate_priority_analysis(courses, students)

    Path("analysis").mkdir(exist_ok=True)

    priority_analysis = priority_analysis.sort_values(
        ["popularity_ratio", "cutoff_priority"],
        ascending=[False, True],
        na_position="last"
    )

    priority_analysis.to_csv(
        "analysis/course_priority_analysis.csv",
        index=False,
        encoding="utf-8-sig"
    )

    students_with_rate = add_student_estimated_accept_rate(
        students,
        priority_analysis
    )

    students_with_rate.to_csv(
        "analysis/student_estimated_accept_rate.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("===== 課程志願序門檻分析前 10 名 =====")

    show_cols = [
        "course_id",
        "course_name",
        "maximum_number",
        "number_of_assigned",
        "number_of_assigned_source_status",
        "popularity_ratio",
        "priority_1_count",
        "cutoff_priority",
        "cutoff_accept_rate",
        "analysis_status",
        "data_warning",
        "recommendation"
    ]

    existing_show_cols = [col for col in show_cols if col in priority_analysis.columns]
    print(priority_analysis[existing_show_cols].head(10))

    print("\n已輸出：analysis/course_priority_analysis.csv")
    print("已輸出：analysis/student_estimated_accept_rate.csv")


if __name__ == "__main__":
    main()
