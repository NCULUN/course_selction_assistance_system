import requests
from pathlib import Path
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://cis.ncu.edu.tw/Course/main/support/courseDetail.html?crs=9044"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(
    url,
    headers=headers,
    verify=False,
    timeout=10
)

res.encoding = "utf-8"

print("狀態碼：", res.status_code)
print(res.text[:500])

Path("raw").mkdir(exist_ok=True)

with open("raw/course_9044.html", "w", encoding="utf-8") as f:
    f.write(res.text)

print("已儲存 raw/course_9044.html")