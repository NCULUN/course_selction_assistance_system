import pandas as pd
from pathlib import Path


def main():
    courses_path = Path("output/courses.csv")
    students_path = Path("output/course_students.csv")

    courses = pd.read_csv(courses_path)
    students = pd.read_csv(students_path)

    # 轉成數字，避免 CSV 讀進來是文字
    courses["maximum_number"] = pd.to_numeric(courses["maximum_number"], errors="coerce")
    courses["number_of_assigned"] = pd.to_numeric(courses["number_of_assigned"], errors="coerce")
    courses["number_of_selected"] = pd.to_numeric(courses["number_of_selected"], errors="coerce")

    # 熱門度：登記人數 / 人數限制
    courses["popularity_ratio"] = courses["number_of_assigned"] / courses["maximum_number"]

    # 超額人數：登記人數 - 人數限制
    courses["over_capacity"] = courses["number_of_assigned"] - courses["maximum_number"]

    # 依熱門度排序
    popular_courses = courses.sort_values("popularity_ratio", ascending=False)

    Path("analysis").mkdir(exist_ok=True)

    popular_courses.to_csv(
        "analysis/popular_courses.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("===== 熱門課程前 10 名 =====")

    show_cols = [
        "course_id",
        "course_name",
        "instructor",
        "maximum_number",
        "number_of_assigned",
        "number_of_selected",
        "popularity_ratio",
        "over_capacity"
    ]

    print(popular_courses[show_cols].head(10))

    print("\n已輸出 analysis/popular_courses.csv")


if __name__ == "__main__":
    main()