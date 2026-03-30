import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, time
from ics import Calendar, Event
import re
import pytz

def crawl_menu_and_generate_ics():
    url = "https://hqb.sxist.edu.cn/info/1381/6404.htm"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "lxml")

    # ===== 1️⃣ 解析标题获取日期 =====
    title = soup.title.get_text(strip=True)
    print("📄 标题：", title)
    match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日).*?(\d{4}年\d{1,2}月\d{1,2}日)", title)
    if not match:
        print("❌ 标题解析失败")
        return
    start_str = match.group(1)
    start_date = datetime.strptime(start_str, "%Y年%m月%d日")
    print("📅 起始日期：", start_date.date())

    # ===== 2️⃣ 解析表格 =====
    tables = soup.find_all("table")
    all_data = {}

    week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        week = None
        for row in rows[:2]:
            text = row.get_text(strip=True)
            for w in week_list:
                if w in text:
                    week = w
                    break
            if week:
                break
        if not week:
            continue
        day_data = {}
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            meal_type = cols[0].get_text(strip=True)
            content = cols[1].get_text("\n", strip=True)
            if meal_type and content:
                day_data[meal_type] = content
        if day_data:
            all_data[week] = day_data

    print("📊 解析结果：", all_data)
    if not all_data:
        print("❌ 没解析到菜单数据")
        return

    # ===== 3️⃣ 生成 ICS =====


    cal = Calendar()

    # 星期顺序
    week_order = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    # 餐次时间
    meal_time_map = {
        "早 餐": ("早餐", time(7, 0)),
        "午 餐": ("午餐", time(11, 0)),
        "晚 餐": ("晚餐", time(17, 0)),
    }

    start_date = datetime.strptime("2026年3月30日", "%Y年%m月%d日")

    for week_name in week_order:

        if week_name not in all_data:
            continue

        day_index = week_order.index(week_name)
        current_date = start_date + timedelta(days=day_index)

        meals = all_data[week_name]

        for raw_meal_name, content in meals.items():

            # 处理“早 餐”这种空格问题
            clean_key = raw_meal_name.replace(" ", "")

            if raw_meal_name in meal_time_map:
                meal_name, meal_time = meal_time_map[raw_meal_name]
            elif clean_key in meal_time_map:
                meal_name, meal_time = meal_time_map[clean_key]
            else:
                continue

            event = Event()

            # ✅ 正确时间（关键）
            # event.begin = datetime.combine(current_date, meal_time)
            tz = pytz.timezone("Asia/Shanghai")

            event.begin = tz.localize(datetime.combine(current_date, meal_time))
            # ✅ 短时长（避免合并/误识别）
            event.duration = timedelta(minutes=20)

            # ❗ 禁止全天
            event.make_all_day = False

            # ❗ 无提醒
            event.alarms = []

            # ✅ 标题：只保留“早餐/午餐/晚餐”
            event.name = meal_name

            event.description = content

            # 唯一ID
            event.uid = f"{week_name}-{meal_name}-{current_date.date()}"

            cal.events.add(event)

    with open("menu.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("✅ 日历生成完成")

if __name__ == "__main__":
    crawl_menu_and_generate_ics()