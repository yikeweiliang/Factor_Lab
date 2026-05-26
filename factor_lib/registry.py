FACTOR_MAP = {}

def register_factor(name, MTW):
    def decorator(func):
        FACTOR_MAP[name] = (func, MTW)
        return func
    return decorator

def get_factor(name):
    """根据名字获取因子计算函数"""
    if name not in FACTOR_MAP:
        raise ValueError(f"因子 {name} 不存在，可用因子: {list(FACTOR_MAP.keys())}")
    return FACTOR_MAP[name]

def list_all_factors():
    """查看所有可用因子"""
    return list(FACTOR_MAP.keys())