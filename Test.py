import subprocess

import os
#
# item_root_path = "item_groups/"
# dataset="Gowalla"
# igroup="020"
# item_groups_path = os.path.join(item_root_path, dataset, igroup)
# # command = f'Invoke-WebRequest -Uri https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/items/{igroup}/shorthead_items.txt -OutFile "{item_groups_path}/shorthead_items.txt"'
# # subprocess.run(["powershell", "-Command", command])
#
# url = "https://raw.githubusercontent.com/rahmanidashti/CPFairRecSys/main/datasets/{dataset}/groups/items/{igroup}/shorthead_items.txt"
#
# # 构建并执行curl命令
# command = f'curl -o "{item_groups_path}/shorthead_items.txt" -L {url}'
# os.system(command)

# from tqdm import tqdm
# import time
#
# total_users = 100
#
# # 使用tqdm显示进度条
# for user_id in tqdm(range(total_users)):
#     # 模拟处理任务
#     time.sleep(0.1)



# import pulp
# 
# # 创建一个整数规划问题
# problem = pulp.LpProblem("MyIntegerProblem", pulp.LpMaximize)
# 
# # 定义变量
# x1 = pulp.LpVariable("x1", lowBound=0, cat="Integer")
# x2 = pulp.LpVariable("x2", lowBound=0, cat="Integer")
# 
# # 定义目标函数
# problem += 4 * x1 + 3 * x2, "Objective"
# 
# # 添加约束条件
# problem += 2 * x1 + x2 <= 5, "Constraint 1"
# problem += x1 + 3 * x2 <= 8, "Constraint 2"
# 
# # 求解整数规划问题
# problem.solve()
# 
# # 打印结果
# print("Status:", pulp.LpStatus[problem.status])
# print("x1 =", x1.varValue)
# print("x2 =", x2.varValue)
# print("Objective =", pulp.value(problem.objective))