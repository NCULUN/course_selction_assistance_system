import requests
from pathlib import Path
import urllib3
from bs4 import BeautifulSoup
import csv
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0"
}


# 課程基本資料的相關函式
def clean_text(text):
    """
    清理多餘空白、換行、tab
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_between(text, start_key, end_keys):
    """
    從一整段文字中，抓出 start_key 後面到下一個 end_key 前面的內容
    """
    start_index = text.find(start_key)

    if start_index == -1:
        return ""

    start_index += len(start_key)

    end_index = len(text)

    for key in end_keys:
        temp_index = text.find(key, start_index)

        if temp_index != -1:
            end_index = min(end_index, temp_index)

    return text[start_index:end_index].strip()


def parse_course_info(crs_id):
    """
    解析課程基本資料
    回傳一個 dict
    """
    html_path = Path(f"raw/course_{crs_id}.html")

    if not html_path.exists():
        raise FileNotFoundError(f"找不到檔案：{html_path}，請先執行 fetch_course_detail({crs_id})")

    html = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    # 取得整頁文字
    text = soup.get_text(" ", strip=True)
    text = clean_text(text)

    # 只取 Course Information 到 Teaching goal 之前
    # 避免抓到後面的課程大綱、評分方式、修課名單
    course_info_text = extract_between(
        text,
        "Course Information",
        ["Teaching goal", "Teaching content", "Textbooks/References", "修課名單"]
    )

    course_info = {
        "course_id": crs_id,

        "serial_number_course_code": extract_between(
            course_info_text,
            "Serial Number / Course Code",
            ["Course Name"]
        ),

        "course_name": extract_between(
            course_info_text,
            "Course Name",
            ["Instructor"]
        ),

        "instructor": extract_between(
            course_info_text,
            "Instructor",
            ["Department"]
        ),

        "department": extract_between(
            course_info_text,
            "Department",
            ["Educational System"]
        ),

        "educational_system": extract_between(
            course_info_text,
            "Educational System",
            ["Time/Building and Room Number"]
        ),

        "time_room": extract_between(
            course_info_text,
            "Time/Building and Room Number",
            ["Required or Elective"]
        ),

        "required_or_elective": extract_between(
            course_info_text,
            "Required or Elective",
            ["Credit"]
        ),

        "credit": extract_between(
            course_info_text,
            "Credit",
            ["Whole Year or Semester"]
        ),

        "semester_type": extract_between(
            course_info_text,
            "Whole Year or Semester",
            ["Lecture Language"]
        ),

        "lecture_language": extract_between(
            course_info_text,
            "Lecture Language",
            ["Code Card Required/Not Required"]
        ),

        "code_card": extract_between(
            course_info_text,
            "Code Card Required/Not Required",
            ["Maximum Number"]
        ),

        "maximum_number": extract_between(
            course_info_text,
            "Maximum Number",
            ["Number of Assigned"]
        ),

        "number_of_assigned": extract_between(
            course_info_text,
            "Number of Assigned",
            ["Number of Selected"]
        ),

        "number_of_selected": extract_between(
            course_info_text,
            "Number of Selected",
            ["Remark", "Teaching goal"]
        ),
    }

    return course_info


def save_course_info_to_csv(course_info):
    """
    將單一課程基本資料存成 CSV
    """
    if not course_info:
        print("沒有課程基本資料可存成 CSV")
        return

    Path("output").mkdir(exist_ok=True)
    csv_path = Path(f"output/course_{course_info['course_id']}_info.csv")

    fieldnames = [
        "course_id",
        "serial_number_course_code",
        "course_name",
        "instructor",
        "department",
        "educational_system",
        "time_room",
        "required_or_elective",
        "credit",
        "semester_type",
        "lecture_language",
        "code_card",
        "maximum_number",
        "number_of_assigned",
        "number_of_selected"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(course_info)

    print(f"已儲存課程基本資料 CSV：{csv_path}")


# 以下是修課名單的相關函式
def fetch_course_detail(crs_id):
    """
    下載課程詳細頁 HTML，存到 raw/course_{crs_id}.html
    """
    url = f"https://cis.ncu.edu.tw/Course/main/support/courseDetail.html?crs={crs_id}"

    res = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    res.encoding = "utf-8"

    print(f"課程 {crs_id} 狀態碼：{res.status_code}")

    Path("raw").mkdir(exist_ok=True)
    file_path = Path(f"raw/course_{crs_id}.html")

    file_path.write_text(res.text, encoding="utf-8")

    print(f"已儲存 {file_path}")

    return file_path


def get_row_cells(row):
    """
    將一列 tr 裡面的 th / td 轉成文字 list
    """
    cols = row.find_all(["th", "td"])
    return [col.get_text(" ", strip=True) for col in cols]


def find_student_table(tables):
    """
    從所有 table 中找出真正的修課名單 table。

    不只判斷整個 table_text 是否包含 Student ID Number，
    而是檢查是否存在一列表頭，且欄位結構符合修課名單。
    """
    expected_headers = [
        "#",
        "Student ID Number",
        "Name",
        "Department",
        "Class",
        "Gender",
        "Required or Elective",
        "Priority",
        "Status of Course Selection"
    ]

    candidates = []

    for i, table in enumerate(tables):
        rows = table.find_all("tr")

        for row in rows:
            cells = get_row_cells(row)

            if cells == expected_headers:
                candidates.append((i, table))
                break

    if not candidates:
        return None

    # 如果有多個 table 都包含這個表頭，選文字量最短的那個
    # 避免選到最外層大 table
    best_i, best_table = min(
        candidates,
        key=lambda item: len(item[1].get_text(" ", strip=True))
    )

    print(f"找到修課名單 table：第 {best_i} 個 table")

    return best_table


def parse_student_list(crs_id):
    """
    解析指定課程的修課名單
    回傳 list[dict]
    """
    html_path = Path(f"raw/course_{crs_id}.html")

    if not html_path.exists():
        raise FileNotFoundError(f"找不到檔案：{html_path}，請先執行 fetch_course_detail({crs_id})")

    html = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    print(f"共找到 {len(tables)} 個 table")

    student_table = find_student_table(tables)

    if student_table is None:
        print("找不到修課名單 table")
        return []

    rows = student_table.find_all("tr")

    students = []

    for row in rows:
        data = get_row_cells(row)

        if len(data) != 9:
            continue

        # 跳過表頭
        if data[0] == "#" and data[1] == "Student ID Number":
            continue

        # 避免誤抓到非學生資料
        # 正常學生列第一欄應該是序號，例如 1、2、3
        if not data[0].isdigit():
            continue

        student = {
            "course_id": crs_id,
            "no": data[0],
            "student_id": data[1],
            "name": data[2],
            "department": data[3],
            "class_name": data[4],
            "gender": data[5],
            "required_or_elective": data[6],
            "priority": data[7],
            "status": data[8]
        }

        students.append(student)

    return students


def save_students_to_csv(students, crs_id):
    """
    將修課名單存成 CSV
    """
    if not students:
        print("沒有資料可存成 CSV")
        return

    Path("output").mkdir(exist_ok=True)
    csv_path = Path(f"output/course_{crs_id}_students.csv")

    fieldnames = [
        "course_id",
        "no",
        "student_id",
        "name",
        "department",
        "class_name",
        "gender",
        "required_or_elective",
        "priority",
        "status"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(students)

    print(f"已儲存 CSV：{csv_path}")


def main():
    crs_id = 9044

    # 1. 下載 HTML
    fetch_course_detail(crs_id)

    # 2. 解析課程基本資料
    course_info = parse_course_info(crs_id)

    print("\n===== 課程基本資料 =====")
    for key, value in course_info.items():
        print(f"{key}: {value}")

    save_course_info_to_csv(course_info)

    # 3. 解析修課名單
    students = parse_student_list(crs_id)

    print(f"\n修課名單人數：{len(students)}")

    for student in students[:5]:
        print(student)

    save_students_to_csv(students, crs_id)


if __name__ == "__main__":
    main()