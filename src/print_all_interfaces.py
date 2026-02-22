import akshare as ak

all_funcs = dir(ak)

with open("akshare_all_interfaces.txt", "w") as f:
    for name in sorted(all_funcs):
        f.write(name + "\n")

print("已导出所有接口到 akshare_all_interfaces.txt")