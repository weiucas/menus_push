import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


def crawl_menu():
    url = "https://hqb.sxist.edu.cn/info/1381/6404.htm"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "lxml")

    # ===== 1️⃣ 获取标题 =====
    title = soup.title.get_text(strip=True)

    # ===== 2️⃣ 提取日期范围 =====
    match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)-(\d{4}年\d{1,2}月\d{1,2}日)", title)

    if not match:
        print("❌ 未识别时间范围")
        return

    start_str, end_str = match.groups()

    start_date = datetime.strptime(start_str, "%Y年%m月%d日")
    end_date = datetime.strptime(end_str, "%Y年%m月%d日")
    # print(start_date, "-", end_date)

    today = datetime.today()

    # ===== 3️⃣ 判断是否在当前周 =====
    if not (start_date <= today <= end_date):
        print("❌ 当前不在菜单时间范围内")
        return

    print(f"✅ 当前菜单有效：{title}")

    # ===== 4️⃣ 解析菜单 =====
    tables = soup.find_all("table")
    all_data = {}

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 2:
            continue

        # 找星期
        week = None
        for row in rows[:2]:
            text = row.get_text(strip=True)
            if "星期" in text:
                week = text.replace(" ", "")
                break

        if not week:
            continue

        day_data = {}

        for row in rows:
            cols = row.find_all("td")

            if len(cols) != 2:
                continue

            meal_type = cols[0].get_text(strip=True)
            content = cols[1].get_text("\n", strip=True)

            day_data[meal_type] = content

        all_data[week] = day_data

    # ===== 5️⃣ 判断今天星期几 =====
    week_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日"
    }

    today_week = week_map[today.weekday()]

    # ===== 6️⃣ 输出今日菜单 =====
    if today_week not in all_data:
        print(f"❌ 未找到 {today_week} 菜单")
        return

    print(f"\n📅 今日菜单（{today_week}）\n")

    for meal, content in all_data[today_week].items():
        print(f"【{meal}】")
        print(content)
        print()


if __name__ == "__main__":
    crawl_menu()
