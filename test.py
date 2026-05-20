import numpy as np
from backtest import backtest, step_to_next_time

# === 四日价格数据（3只股票 + 现金占位）===
# 每行: [现金价格(占位), 股票A, 股票B, 股票C]
prices = np.array([
    [1.0, 10.0, 20.0, 50.0],   # 第0天初始价格
    [1.0, 12.0, 18.0, 55.0],   # 第1天
    [1.0, 11.0, 22.0, 48.0],   # 第2天
    [1.0, 13.0, 19.0, 52.0],   # 第3天
])

# === 每天的期望权重（第一列是现金）===
target_weights = np.array([
    [0.2, 0.4, 0.1, 0.3],   # 第0天目标
    [0.1, 0.3, 0.4, 0.2],   # 第1天目标
    [0.3, 0.2, 0.3, 0.2],   # 第2天目标
    [0.1, 0.5, 0.2, 0.2],   # 第3天目标
])

# 全可交易
restrictions = np.array([
    [True, True, True, True],
    [True, False, True, True],
    [True, True, False, True],
    [True, True, True, False]
])

initial_money = 100000.0
initial_shares = np.array([100000.0, 0, 0, 0])  # 第0天初始股数

print("=" * 60)
print("多期回测测试（4天，3只股票）")
print("=" * 60)

# ----- 第0天：首次调仓 -----
bt0 = step_to_next_time(initial_shares, prices[0])
m0, w0 = bt0.step()
bt0_backtest = backtest(m0, w0, restrictions[0], target_weights[0], prices[0])
w0, s0 = bt0_backtest.run_backtest_onetime()
print(f"📅 第0天")
print(f"   价格: {prices[0][1:]}")
print(f"   初始全现金 → 调仓到目标权重: {target_weights[0]}")
print(f"   最终权重: {np.round(w0, 4)}  (总和={np.sum(w0):.4f})")
print(f"   持仓股数: {s0[1:].astype(int)}  现金: {s0[0]:.2f}  市值: {np.sum(s0):.2f}")

# 用第0天的调仓结果作为第1天的起点，依次类推
current_shares = s0

# ----- 第1天：价格变动 → 调仓 -----
st1 = step_to_next_time(current_shares, prices[1])
m1, w1_before = st1.step()
bt1 = backtest(m1, w1_before, restrictions[1], target_weights[1], prices[1])
w1, s1 = bt1.run_backtest_onetime()
print(f"\n📅 第1天")
print(f"   价格: {prices[1][1:]}")
print(f"   调仓前权重: {np.round(w1_before, 4)}  目标: {target_weights[1]}")
print(f"   调仓后权重: {np.round(w1, 4)}  (总和={np.sum(w1):.4f})")
print(f"   持仓股数: {s1[1:].astype(int)}  现金: {s1[0]:.2f}  市值: {np.sum(s1):.2f}")

current_shares = s1

# ----- 第2天：价格变动 → 调仓 -----
st2 = step_to_next_time(current_shares, prices[2])
m2, w2_before = st2.step()
bt2 = backtest(m2, w2_before, restrictions[2], target_weights[2], prices[2])
w2, s2 = bt2.run_backtest_onetime()
print(f"\n📅 第2天")
print(f"   价格: {prices[2][1:]}")
print(f"   调仓前权重: {np.round(w2_before, 4)}  目标: {target_weights[2]}")
print(f"   调仓后权重: {np.round(w2, 4)}  (总和={np.sum(w2):.4f})")
print(f"   持仓股数: {s2[1:].astype(int)}  现金: {s2[0]:.2f}  市值: {np.sum(s2):.2f}")

current_shares = s2

# ----- 第3天：价格变动 → 调仓 -----
st3 = step_to_next_time(current_shares, prices[3])
m3, w3_before = st3.step()
bt3 = backtest(m3, w3_before, restrictions[3], target_weights[3], prices[3])
w3, s3 = bt3.run_backtest_onetime()
print(f"\n📅 第3天")
print(f"   价格: {prices[3][1:]}")
print(f"   调仓前权重: {np.round(w3_before, 4)}  目标: {target_weights[3]}")
print(f"   调仓后权重: {np.round(w3, 4)}  (总和={np.sum(w3):.4f})")
print(f"   持仓股数: {s3[1:].astype(int)}  现金: {s3[0]:.2f}  市值: {np.sum(s3):.2f}")
