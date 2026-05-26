import pandas as pd
import h5py
import akshare as ak
import os
import time
import requests

_frequency_registry = {}

def register_frequency(freq):
    def decorator(func):
        _frequency_registry[freq] = func
        return func
    return decorator

# 中文字段名到英文字段名的映射
_COLUMN_RENAME_MAP = {
    '日期': 'date',
    '股票代码': 'code',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount',
    '振幅': 'amplitude',
    '涨跌幅': 'pct_change',
    '涨跌额': 'change',
    '换手率': 'turnover',
}


def _clean_and_save(df: pd.DataFrame, filepath: str) -> None:
    """统一处理 DataFrame：重命名列、转换日期、删除冗余列、保存到 HDF5"""
    # 重命名中文字段 → 英文字段
    df.rename(columns=_COLUMN_RENAME_MAP, inplace=True)

    # 日期列转 datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # 删除冗余的 'code' 列（已通过文件名标识股票）
    if 'code' in df.columns:
        df.drop(columns=['code'], inplace=True)

    df.to_hdf(filepath, key='data', mode='w', format='table')


def _fetch_with_retry(fetch_func, stock: str, max_retries: int = 3):
    """带指数退避重试的数据获取函数"""
    for attempt in range(max_retries):
        try:
            df = fetch_func()
            return df
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            if attempt == max_retries - 1:
                print(f"  ⚠️ {stock} 下载失败（已重试 {max_retries} 次）: {e}")
                raise
            wait = (attempt + 1) * 2
            print(f"  ⚠️ {stock} 重试第 {attempt + 1} 次，等待 {wait}s ...")
            time.sleep(wait)


class stock_data_load_daily:

    def __init__(self, stock_list: list, start_date: str, end_date: str,
                 fq: str, frequency: str = 'daily'):
        self.stock_list = stock_list
        self.start_date = start_date
        self.end_date = end_date
        self.fq = fq
        self.frequency = frequency
        base_dir = os.path.join(os.path.dirname(__file__), 'data_resource')
        self.data_dir = base_dir

    @register_frequency('daily')
    def load_data_daily(self):
        for stock in self.stock_list:
            filepath = os.path.join(self.data_dir, f'{stock}_{self.frequency}_{self.fq}.h5')
            if os.path.exists(filepath):
                print(f"  ✓ {stock} 已存在，跳过")
                continue

            def fetch():
                return ak.stock_zh_a_hist(
                    symbol=stock,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    adjust=self.fq
                )

            try:
                df = _fetch_with_retry(fetch, stock)
                _clean_and_save(df, filepath)
                print(f"  ✓ {stock} 下载完成")
            except Exception as e:
                print(f"  ✗ {stock} 最终下载失败: {e}")
            finally:
                time.sleep(0.3)  # 请求间延迟

    @register_frequency('15min')
    def load_data_15min(self):
        for stock in self.stock_list:
            filepath = os.path.join(self.data_dir, f'{stock}_{self.frequency}_{self.fq}.h5')
            if os.path.exists(filepath):
                print(f"  ✓ {stock} 已存在，跳过")
                continue

            def fetch():
                return ak.stock_zh_a_15min(
                    symbol=stock,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    adjust=self.fq
                )

            try:
                df = _fetch_with_retry(fetch, stock)
                _clean_and_save(df, filepath)
                print(f"  ✓ {stock} 下载完成")
            except Exception:
                pass
            finally:
                time.sleep(0.3)

    def load_data(self):
        method = _frequency_registry.get(self.frequency)
        if method is None:
            raise ValueError(f"不支持的 frequency 值: {self.frequency}")
        return method(self)