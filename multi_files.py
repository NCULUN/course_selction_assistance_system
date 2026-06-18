import requests
from pathlib import Path
import urllib3
from bs4 import BeautifulSoup
import csv
import re
from time import sleep
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0"
}


def save_all_course_info_to_csv(course_infos):
    """
    將多門課的基本資料存成同一份 courses.csv
    """
    if not course_infos:
        print("沒有課程基本資料可存成 CSV")
        return

    Path("output").mkdir(exist_ok=True)
    csv_path = Path("output/courses.csv")

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
        writer.writerows(course_infos)

    print(f"已儲存所有課程基本資料：{csv_path}")


def save_all_students_to_csv(all_students):
    """
    將多門課的修課名單存成同一份 course_students.csv
    """
    if not all_students:
        print("沒有修課名單資料可存成 CSV")
        return

    Path("output").mkdir(exist_ok=True)
    csv_path = Path("output/course_students.csv")

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
        writer.writerows(all_students)

    print(f"已儲存所有修課名單：{csv_path}")


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
def fetch_course_detail(crs_id, use_cache=True):
    """
    下載課程詳細頁 HTML，存到 raw/course_{crs_id}.html

    use_cache=True 時：
    如果本機已經有 raw/course_{crs_id}.html，就不重新下載。
    """
    Path("raw").mkdir(exist_ok=True)
    file_path = Path(f"raw/course_{crs_id}.html")

    if use_cache and file_path.exists():
        print(f"課程 {crs_id} 已有快取，使用本機檔案：{file_path}")
        return file_path

    url = f"https://cis.ncu.edu.tw/Course/main/support/courseDetail.html?crs={crs_id}"

    res = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    res.encoding = "utf-8"

    print(f"課程 {crs_id} 狀態碼：{res.status_code}")

    if res.status_code != 200:
        raise Exception(f"課程 {crs_id} 下載失敗，狀態碼：{res.status_code}")

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
    crs_ids = list(range(9001, 9062))  # 這裡可以放多個課程代碼

    all_course_infos = []
    all_students = []
    failed_courses = []

    for crs_id in crs_ids:
        print("\n" + "=" * 80)
        print(f"開始處理課程：{crs_id}")

        try:
            # 1. 下載 HTML，若 raw 裡已經有檔案就使用快取
            fetch_course_detail(crs_id, use_cache=True)

            # 2. 解析課程基本資料
            course_info = parse_course_info(crs_id)

            # 如果沒有課程名稱，通常代表這個 crs_id 不是有效課程頁
            if not course_info.get("course_name"):
                print(f"課程 {crs_id} 沒有抓到課程名稱，略過")
                failed_courses.append((crs_id, "沒有抓到課程名稱"))
                continue

            all_course_infos.append(course_info)

            print("\n===== 課程基本資料 =====")
            print("course_id:", course_info["course_id"])
            print("course_name:", course_info["course_name"])
            print("instructor:", course_info["instructor"])
            print("maximum_number:", course_info["maximum_number"])
            print("number_of_assigned:", course_info["number_of_assigned"])
            print("number_of_selected:", course_info["number_of_selected"])

            # 3. 解析修課名單
            students = parse_student_list(crs_id)
            all_students.extend(students)

            print(f"修課名單人數：{len(students)}")

            # 4. 做簡單檢查：待分發人數是否等於修課名單筆數
            assigned_count = str(course_info["number_of_assigned"]).strip()

            if assigned_count.isdigit():
                if int(assigned_count) == len(students):
                    print("資料檢查：待分發人數與修課名單人數一致")
                else:
                    print("資料檢查：待分發人數與修課名單人數不一致")
                    print("number_of_assigned:", assigned_count)
                    print("students:", len(students))

        except Exception as e:
            print(f"課程 {crs_id} 發生錯誤：{e}")
            failed_courses.append((crs_id, str(e)))

        # 避免太密集發 request
        sleep(15)

    # 5. 儲存總表
    save_all_course_info_to_csv(all_course_infos)
    save_all_students_to_csv(all_students)

    # 6. 儲存失敗清單
    if failed_courses:
        Path("output").mkdir(exist_ok=True)
        failed_path = Path("output/failed_courses.txt")

        with open(failed_path, "w", encoding="utf-8") as f:
            for crs_id, reason in failed_courses:
                f.write(f"{crs_id}: {reason}\n")

        print(f"失敗課程清單已儲存：{failed_path}")

    print("\n===== 批次完成 =====")
    print("成功課程數：", len(all_course_infos))
    print("總修課資料筆數：", len(all_students))
    print("失敗課程數：", len(failed_courses))


if __name__ == "__main__":
    main()