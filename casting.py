"""三枚铜钱法起卦模块。

模拟三枚铜钱抛6次，生成本卦六爻和变爻信息。
"""

import random
from dataclasses import dataclass, field

from gua_data import GUA_BY_BINARY, GuaInfo

POINT_MAP: dict[str, int] = {"正面": 3, "反面": 2}


@dataclass
class CastingResult:
    """起卦结果。"""

    lines: list[int]           # 本卦六爻，0=阴 1=阳，索引0=初爻
    changing_lines: list[int]  # 变爻位置索引列表，[0..5]
    has_changing: bool          # 是否有变爻
    changed_lines: list[int] = field(init=False)  # 变卦六爻（如有）

    def __post_init__(self) -> None:
        self.changed_lines = list(self.lines)
        for pos in self.changing_lines:
            self.changed_lines[pos] = 1 - self.changed_lines[pos]


def _toss_coin() -> str:
    """模拟一枚铜钱，返回 '正面' 或 '反面'。"""
    return random.choice(["正面", "反面"])


def _toss_three_coins() -> tuple[int, bool]:
    """掷三枚铜钱，返回 (爻象值 0/1, 是否为变爻)。"""
    total = sum(POINT_MAP[_toss_coin()] for _ in range(3))

    mapping: dict[int, tuple[int, bool]] = {
        6: (0, True),   # 老阴 → 阴，变爻
        7: (1, False),  # 少阳 → 阳，不变
        8: (0, False),  # 少阴 → 阴，不变
        9: (1, True),   # 老阳 → 阳，变爻
    }
    return mapping[total]


def cast() -> CastingResult:
    """执行一次完整的起卦（掷6次），返回起卦结果。"""
    lines: list[int] = []
    changing_lines: list[int] = []

    for i in range(6):
        value, is_changing = _toss_three_coins()
        lines.append(value)
        if is_changing:
            changing_lines.append(i)

    return CastingResult(
        lines=lines,
        changing_lines=changing_lines,
        has_changing=len(changing_lines) > 0,
    )


def lines_to_binary(lines: list[int]) -> int:
    """将六爻列表（初爻索引0）转为6位二进制编码。"""
    return sum(b << i for i, b in enumerate(lines))


def lookup_gua(lines: list[int]) -> GuaInfo:
    """根据六爻查找本卦信息。"""
    binary = lines_to_binary(lines)
    return GUA_BY_BINARY[binary]


def lookup_changed_gua(changed_lines: list[int]) -> GuaInfo:
    """根据变卦六爻查找变卦信息。"""
    binary = lines_to_binary(changed_lines)
    return GUA_BY_BINARY[binary]


__all__ = [
    "CastingResult",
    "cast",
    "lines_to_binary",
    "lookup_gua",
    "lookup_changed_gua",
]