import pandas as pd
from pathlib import Path


def calculate_priority_analysis(courses, students):
    results = []

    for _, course in courses.iterrows():
        course_id = course["course_id"]

        capacity = pd.to_numeric(course["maximum_number"], errors="coerce")
        assigned = pd.to_numeric(course["number_of_assigned"], errors="coerce")

        course_students = students[students["course_id"] == course_id].copy()

        if pd.isna(capacity) or capacity <= 0:
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

        if cutoff_priority is None:
            recommendation = "報名資料不足，無法判斷"
            no_chance_after_priority = ""
        elif len(course_students) <= capacity:
            recommendation = "報名人數未超過容量，各志願序皆有機會"
            no_chance_after_priority = ""
        else:
            recommendation = f"建議填在第 {cutoff_priority} 志願以內才有機會"
            no_chance_after_priority = cutoff_priority

        results.append({
            "course_id": course_id,
            "course_name": course.get("course_name", ""),
            "instructor": course.get("instructor", ""),
            "time_room": course.get("time_room", ""),
            "maximum_number": int(capacity),
            "number_of_assigned": int(assigned) if not pd.isna(assigned) else len(course_students),
            "priority_1_count": priority_1_count,
            "cutoff_priority": cutoff_priority,
            "cutoff_priority_count": cutoff_priority_count,
            "seats_before_cutoff": seats_before_cutoff,
            "seats_remaining_at_cutoff": seats_remaining_at_cutoff,
            "cutoff_accept_rate": round(cutoff_accept_rate, 3),
            "recommended_max_priority": cutoff_priority,
            "no_chance_after_priority": no_chance_after_priority,
            "recommendation": recommendation
        })

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
                "cutoff_accept_rate"
            ]
        ],
        on="course_id",
        how="left"
    )

    def estimate(row):
        priority = row["priority"]
        cutoff = row["cutoff_priority"]
        cutoff_rate = row["cutoff_accept_rate"]

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

    # 依「門檻志願序中選率」由低到高排序：越難中的課越排前面
    priority_analysis = priority_analysis.sort_values(
        ["cutoff_accept_rate", "cutoff_priority"],
        ascending=[True, True]
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
        "priority_1_count",
        "cutoff_priority",
        "cutoff_priority_count",
        "seats_remaining_at_cutoff",
        "cutoff_accept_rate",
        "recommendation"
    ]

    print(priority_analysis[show_cols].head(10))

    print("\n已輸出：analysis/course_priority_analysis.csv")
    print("已輸出：analysis/student_estimated_accept_rate.csv")


if __name__ == "__main__":
    main()
