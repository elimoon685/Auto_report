import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time

INDEX_URL = "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/5727710/index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def month_to_int(yyyymm):
    y = int(yyyymm[:4])
    m = int(yyyymm[4:])
    return y * 12 + m


def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.encoding = r.apparent_encoding
    return r.text


def get_month_links():
    html = fetch_html(INDEX_URL)
    soup = BeautifulSoup(html, "lxml")

    links = []

    for a in soup.find_all("a"):
        title = a.get_text(strip=True)
        href = a.get("href")

        if not href:
            continue

        # 找“中央银行各项工具流动性投放情况”
        if "中央银行各项工具流动性投放情况" in title:
            full_url = urljoin(INDEX_URL, href)

            # 从标题里提取年月
            m = re.search(r"(\d{4})年(\d{1,2})月", title)
            if m:
                y = m.group(1)
                mo = m.group(2).zfill(2)
                yyyymm = f"{y}{mo}"
                links.append((yyyymm, full_url))

    return links


def _is_number_cell(x: str) -> bool:
    x = x.replace(",", "").strip()
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", x))

def parse_mlf_from_table(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        for i, row in enumerate(rows):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if not cells:
                continue

            row_text = "".join(cells)

            # ✅ 只锁定 MLF，避免误命中 SLF
            if ("中期借贷便利" not in row_text) and ("MLF" not in row_text.upper()):
                continue
            if ("常备借贷便利" in row_text) or ("SLF" in row_text.upper()):
                continue

            # 1) 先取当前行数字
            nums = []
            for c in cells:
                c2 = c.replace(",", "")
                if _is_number_cell(c2):
                    nums.append(c2)

            # 2) 若不足 3 个，向下继续吃后续行的数字（处理 rowspan 拆行）
            j = i + 1
            while len(nums) < 3 and j < len(rows):
                next_cells = [c.get_text(strip=True) for c in rows[j].find_all(["td", "th"])]
                if not next_cells:
                    j += 1
                    continue

                # 如果下一行已经进入别的工具（例如 PSL / 其他结构性工具 / 公开市场），就停止补齐
                next_text = "".join(next_cells)
                if ("借贷便利" in next_text) or ("PSL" in next_text) or ("公开市场" in next_text) or ("其他结构性" in next_text):
                    break

                for c in next_cells:
                    c2 = c.replace(",", "")
                    if _is_number_cell(c2):
                        nums.append(c2)

                j += 1

            if len(nums) >= 3:
                op, mat, net = float(nums[0]), float(nums[1]), float(nums[2])
                return {"operation": op, "maturity": mat, "net": net}

    return None


def fetch_range(start, end):
    start_i = month_to_int(start)
    end_i = month_to_int(end)

    links = get_month_links()
    results = []

    for yyyymm, url in links:
        m_i = month_to_int(yyyymm)
        if start_i <= m_i <= end_i:
            print(f"抓取 {yyyymm} ...")
            data = parse_mlf_from_table(url)
            if data:
                results.append({
                    "month": yyyymm,
                    "operation_yi": data["operation"],
                    "maturity_yi": data["maturity"],
                    "net_yi": data["net"],
                })
            time.sleep(0.5)

    df = pd.DataFrame(results)
    df = df.sort_values("month")
    return df


if __name__ == "__main__":
    start = "202512"
    end = "202601"

    df = fetch_range(start, end)
    print(df)
    df.to_csv("data/raw/mlf_monthly.csv", index=False, encoding="utf-8-sig")