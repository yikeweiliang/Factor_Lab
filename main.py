
"""
主入口：下载数据 → 计算因子 → 回测
股票池：从 stock_list.csv 读取
"""
import os
import pandas as pd
import numpy as np
from data_load_processing.data_loading import stock_data_load_daily
from data_load_processing.factor_calc import FactorCalc
from trading import TradingEngine

# 从 CSV 读取股票池
csv_path = os.path.join('data_load_processing', 'stock_list.csv')
stock_df = pd.read_csv(csv_path)
clean_stock_list = stock_df['stock_list'].astype(str).tolist()

start_date = '20250101'
end_date = '20251231'
fq = 'qfq'
frequency = 'daily'




def main():
    # ============================================================
    # 1. 股票池 & 参数
    # ============================================================
    print("=" * 60)
    print(f"股票池共 {len(clean_stock_list)} 只股票")
    print(f"时间区间: {start_date} ~ {end_date}")
    print("=" * 60)

    # ============================================================
    # 2. 下载数据
    # ============================================================
    print("\n【Step 1】下载数据 ...")
    os.makedirs('data_load_processing/data_resource', exist_ok=True)

    loader = stock_data_load_daily(
        stock_list=clean_stock_list,
        start_date=start_date,
        end_date=end_date,
        fq=fq,
        frequency=frequency,
    )
    loader.load_data()
    print("下载完毕")

    # ============================================================
    # 3. 计算因子 → final_table
    # ============================================================
    print("\n【Step 2】计算因子 (hl) ...")
    calc = FactorCalc(clean_stock_list, frequency, fq)
    final_table = calc.compute('hl')
    final_table = final_table.reset_index()
    print(f"因子表: {final_table.shape[0]} 天, {final_table.shape[1] - 1} 只股票")

    # ============================================================
    # 4. 构建 price_table 和 volume_table
    # ============================================================
    print("\n【Step 3】构建价格表 & 成交量表 ...")
    price_list = []
    volume_list = []

    for stock in clean_stock_list:
        file_path = f'data_load_processing/data_resource/{stock}_{frequency}_{fq}.h5'
        if not os.path.exists(file_path):
            print(f"  ⚠️ {stock} 文件不存在，跳过")
            continue
        df = pd.read_hdf(file_path, key='data')
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values('date', inplace=True)
        price_list.append(df[['date', 'close']].rename(columns={'close': stock}))
        volume_list.append(df[['date', 'volume']].rename(columns={'volume': stock}))

    price_table = price_list[0]
    for p in price_list[1:]:
        price_table = price_table.merge(p, on='date', how='outer')

    volume_table = volume_list[0]
    for v in volume_list[1:]:
        volume_table = volume_table.merge(v, on='date', how='outer')

    price_table.sort_values('date', inplace=True)
    volume_table.sort_values('date', inplace=True)
    print(f"价格表: {price_table.shape[0]} 天")
    print(f"成交量表: {volume_table.shape[0]} 天")

    # ============================================================
    # 5. 运行回测
    # ============================================================
    print("\n【Step 4】运行回测 ...")
    engine = TradingEngine(
        stock_list=clean_stock_list,
        final_table=final_table,
        price_table=price_table,
        volume_table=volume_table,
        initial_money=1_000_000,
        weight_method='equal_weight',
        log_path='daily_log.csv',
    )
    result_df = engine.run()

    final_value = result_df['total_value'].iloc[-1]
    total_return = (final_value / 1_000_000) - 1
    max_drawdown = _max_drawdown(result_df['total_value'].values)

    print("\n" + "=" * 60)
    print("                   回  测  结  果")
    print("=" * 60)
    print(f"  初始资金:    1,000,000")
    print(f"  最终总资产:  {final_value:>12,.2f}")
    print(f"  总收益率:    {total_return:>12.2%}")
    print(f"  最大回撤:    {max_drawdown:>12.2%}")
    print("=" * 60)


def _max_drawdown(arr: np.ndarray) -> float:
    peak = np.maximum.accumulate(arr)
    drawdown = (arr - peak) / peak
    return abs(drawdown.min())


if __name__ == '__main__':
    main()
