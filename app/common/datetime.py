from __future__ import annotations

import datetime as _dt
from typing import Optional


def current_timestamp_ms(tz: Optional[_dt.tzinfo] = None) -> int:
    """
    获取当前时区的毫秒级时间戳。

    :param tz: 目标时区，为 None 时默认使用本地时区（使用系统配置）。
    :return: 毫秒级时间戳（int）
    """
    # 如果没有显式传入时区，则使用本地时间（含本地时区信息，如果系统支持）
    now = _dt.datetime.now(tz=tz)
    return datetime_to_timestamp_ms(now)


def datetime_to_timestamp_ms(dt: _dt.datetime) -> int:
    """
    将 datetime 对象转换为毫秒级时间戳。

    - 如果是朔源时间（naive datetime），默认按本地时间处理。
    - 如果带有 tzinfo，则使用对应时区进行转换。

    :param dt: datetime 对象
    :return: 毫秒级时间戳（int）
    """
    # Python 的 timestamp() 返回秒级浮点数，这里统一转为毫秒级整数
    ts = dt.timestamp()
    return int(ts * 1000)

