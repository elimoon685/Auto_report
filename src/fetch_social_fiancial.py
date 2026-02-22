import akshare as ak
import pandas as pd
import os

# 1️⃣ 抓取社融数据（官方社融增量表）
df = ak.macro_china_shrzgm()   # 社会融资规模增量

# 看一下列名（第一次可以打开确认）
print("原始列名：")
print(df.columns)

# 2️⃣ 统一月份格式为 YYYYMM
df["月份"] = df["月份"].astype(str)
df["month"] = df["月份"].str.replace("-", "")

# 3️⃣ 选取我们要的四个月
target_months = ["202412", "202501", "202512", "202601"]

df_filtered = df[df["month"].isin(target_months)]

# 4️⃣ 只保留核心4个指标
df_core = df_filtered[[
    "month",
    "社会融资规模增量",
    "其中-人民币贷款",
    "其中-未贴现银行承兑汇票",
    "其中-企业债券"
]]

# 5️⃣ 创建目录并保存
os.makedirs("data/raw", exist_ok=True)

df_core.to_csv(
    "data/raw/social_core_4months.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n====== 四个月核心社融指标 ======")
print(df_core)
print("\n✅ 已生成文件：data/raw/social_core_4months.csv")