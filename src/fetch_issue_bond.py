

import akshare as ak

df = ak.bond_china_yield()
df_cd = df[df["曲线名称"].str.contains("同业存单")]
print(df_cd)
print(df.columns)
print(df.head())
