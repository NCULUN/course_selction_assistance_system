from bs4 import BeautifulSoup
from pathlib import Path

html_path = Path("raw/course_9044.html")

html = html_path.read_text(encoding="utf-8")

soup = BeautifulSoup(html, "html.parser")

# 先看整份網頁純文字
text = soup.get_text("\n", strip=True)

print(text[:2000])