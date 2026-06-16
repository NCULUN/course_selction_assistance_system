import requests
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_course_detail(crs_id):
    url = f"https://cis.ncu.edu.tw/Course/main/support/courseDetail.html?crs={crs_id}"

    res = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=10
    )

    res.encoding = "utf-8"

    print(f"課程 {crs_id} 狀態碼：", res.status_code)

    Path("raw").mkdir(exist_ok=True)

    file_path = f"raw/course_{crs_id}.html"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(res.text)

    print(f"已儲存 {file_path}")

    return res.text


html = fetch_course_detail(9044)
print(html[:500])