import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
from ics import Calendar, Event
import re
from zoneinfo import ZoneInfo  # ✅ 时区


# ===============================
# 1️⃣ 获取最新菜单
# ===============================
def get_latest_menu_url():
    base_url = "https://hqb.sxist.edu.cn/kjtd/cyfw.htm"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url, headers=headers)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "lxml")

    links = soup.select("a")

    menu_links = []

    for a in links:
        text = a.get_text(strip=True)
        if "自助餐菜单" in text:
            href = a.get("href")
            if href:
                full_url = urljoin(base_url, href)
                menu_links.append((text, full_url))

    print("📄 找到菜单数量:", len(menu_links))

    if not menu_links:
        print("❌ 没有找到菜单")
        return None

    latest_menu = menu_links[0]

    print("📌 选择菜单：", latest_menu[0])
    print("🔗 链接：", latest_menu[1])

    return latest_menu[1]


# ===============================
# 2️⃣ 解析菜单（自动日期范围）
# ===============================
def parse_menu(menu_url):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(menu_url, headers=headers)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "lxml")

    title = soup.title.get_text(strip=True)
    print("📄 标题：", title)

    # 提取日期范围
    match = re.search(
        r"(\d{4}年\d{1,2}月\d{1,2}日)-(\d{4}年\d{1,2}月\d{1,2}日)",
        title
    )

    if not match:
        print("❌ 未识别日期范围")
        return None

    start_date = datetime.strptime(match.group(1), "%Y年%m月%d日")
    end_date = datetime.strptime(match.group(2), "%Y年%m月%d日")

    print("📅 起始日期:", start_date.date())
    print("📅 结束日期:", end_date.date())

    tables = soup.find_all("table")

    all_data = {}

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 2:
            continue

        week = None

        for row in rows:
            text = row.get_text(" ", strip=True)
            if "星期" in text:
                week = text
                break

        if not week:
            continue

        # 清洗
        week = week.strip().replace(" ", "")

        day_data = {}

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 2:
                continue

            meal = cols[0].get_text(strip=True)
            content = cols[1].get_text("\n", strip=True)

            if meal:
                day_data[meal] = content

        all_data[week] = day_data

    print("📊 解析结果：", all_data)

    return all_data, start_date, end_date


# ===============================
# 3️⃣ 生成 ICS（含北京时区）
# ===============================
def generate_ics(all_data, start_date, end_date):
    cal = Calendar()

    meal_time = {
        "早 餐": (7, 0),
        "午 餐": (11, 0),
        "晚 餐": (17, 0)
    }

    week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    total_days = (end_date - start_date).days + 1

    tz = ZoneInfo("Asia/Shanghai")  # ✅ 北京时区

    print("📌 all_data keys:", list(all_data.keys()))

    for i in range(total_days):
        current_date = start_date + timedelta(days=i)

        weekday_name = week_map[current_date.weekday()]

        if weekday_name not in all_data:
            print("⚠️ 跳过:", weekday_name)
            continue

        day_data = all_data[weekday_name]

        for meal, content in day_data.items():
            if meal not in meal_time:
                continue

            hour, minute = meal_time[meal]

            event_time = current_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
                tzinfo=tz   # ✅ 关键：时区
            )

            event = Event()
            event.name = f"{current_date.month}-{current_date.day} {meal.replace(' ', '')}"
            event.begin = event_time
            event.duration = timedelta(minutes=30)
            event.description = content

            cal.events.add(event)

    return cal


# ===============================
# 4️⃣ 保存 ICS
# ===============================
def save_ics(cal, filename="menu.ics"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(cal.serialize())  # ✅ 官方推荐


# ===============================
# 5️⃣ 主流程
# ===============================
if __name__ == "__main__":
    url = get_latest_menu_url()

    if not url:
        exit()

    result = parse_menu(url)

    if not result:
        exit()

    all_data, start_date, end_date = result

    cal = generate_ics(all_data, start_date, end_date)

    save_ics(cal)

    print(f"📅 共生成 {len(cal.events)} 个事件")
    print("✅ ICS 生成完成：menu.ics")