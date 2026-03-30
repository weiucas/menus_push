import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, time
import re
from ics import Calendar, Event


def crawl_menu():
    url = "https://hqb.sxist.edu.cn/info/1381/6404.htm"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "lxml")

    # ===== 1️⃣ 标题 =====
    title = soup.title.get_text(strip=True)

    # ===== 2️⃣ 提取日期范围 =====
    match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日)-(\d{4}年\d{1,2}月\d{1,2}日)", title)

    if not match:
        print("❌ 未识别时间范围")
        return

    start_str, end_str = match.groups()

    start_date = datetime.strptime(start_str, "%Y年%m月%d日")
    end_date = datetime.strptime(end_str, "%Y年%m月%d日")

    print(f"📅 菜单周期: {start_date.date()} ~ {end_date.date()}")

    # ===== 3️⃣ 解析菜单 =====
    tables = soup.find_all("table")
    all_data = {}

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 2:
            continue

        week = None

        # 找星期
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

    # ===== 4️⃣ 星期 → 日期映射 =====
    def get_date_by_week(start_date, week_name):
        week_offset = {
            "星期一": 0,
            "星期二": 1,
            "星期三": 2,
            "星期四": 3,
            "星期五": 4,
            "星期六": 5,
            "星期日": 6
        }

        return start_date + timedelta(days=week_offset[week_name])

    # ===== 5️⃣ 创建日历 =====
    cal = Calendar()

    # 餐次时间（可自定义）
    meal_time_map = {
        "早餐": time(8, 0),
        "午餐": time(12, 0),
        "晚餐": time(18, 0)
    }

    # ===== 6️⃣ 生成事件 =====
    for week_name, meals in all_data.items():

        if week_name not in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]:
            continue

        date = get_date_by_week(start_date, week_name)

        for meal_type, content in meals.items():

            event = Event()

            event_time = meal_time_map.get(meal_type, time(12, 0))

            event.begin = datetime.combine(date, event_time)

            event.name = f"{week_name} {meal_type}"
            event.description = content

            # 避免重复（非常重要）
            event.uid = f"{week_name}-{meal_type}-{date.date()}"

            cal.events.add(event)

    # ===== 7️⃣ 输出 ICS =====
    with open("menu.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("✅ 日历文件已生成：menu.ics")


if __name__ == "__main__":
    crawl_menu()