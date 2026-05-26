from .registry import register_factor

@register_factor('momentum_20', MTW = 20)
def momentum_20(df):
    """20日动量因子"""
    return df['close'].pct_change(20)

@register_factor('momentum_60', MTW = 60)
def momentum_60(df):
    """60日动量因子"""
    return df['close'].pct_change(60)

@register_factor('hl', MTW = 0)
def hl(df):
    return (df['high'] - df['low']) / df['close']