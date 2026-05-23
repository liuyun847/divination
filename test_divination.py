"""算卦工具测试。

测试 gua_data 数据完整性、casting 起卦逻辑、interpreter 提示词构建、
以及端到端集成流程（不实际调用 API）。
"""

import random

import pytest

from casting import (
    cast,
    lines_to_binary,
    lookup_gua,
    lookup_changed_gua,
    CastingResult,
)
from gua_data import GUA_DATA, GUA_BY_BINARY, GuaInfo
from interpreter import build_user_prompt, ApiConfig


class TestGuaData:
    """卦数据完整性测试。"""

    def test_count(self) -> None:
        """验证 64 卦数据完整。"""
        assert len(GUA_DATA) == 64
        assert len(GUA_BY_BINARY) == 64

    def test_index_range(self) -> None:
        """验证卦序 1-64。"""
        indices = [g.index for g in GUA_DATA]
        assert sorted(indices) == list(range(1, 65))

    def test_binary_unique_and_complete(self) -> None:
        """验证二进制编码 0-63 全覆盖且唯一。"""
        binaries = [g.binary for g in GUA_DATA]
        assert sorted(binaries) == list(range(64))

    def test_binary_lookup_roundtrip(self) -> None:
        """验证通过二进制查卦与列表查卦一致。"""
        for g in GUA_DATA:
            found = GUA_BY_BINARY[g.binary]
            assert found.index == g.index
            assert found.name == g.name

    def test_symbols(self) -> None:
        """验证 Unicode 卦符正确（文王卦序）。"""
        for g in GUA_DATA:
            assert g.symbol == chr(0x4DC0 + g.index - 1)

    def test_trigram_format(self) -> None:
        """验证上下卦字符串包含卦名和 Unicode 卦符。"""
        for g in GUA_DATA:
            assert len(g.upper) == 2  # 如 "乾☰"
            assert len(g.lower) == 2


class TestCasting:
    """起卦逻辑测试。"""

    def test_cast_has_six_lines(self) -> None:
        """验证起卦生成 6 爻。"""
        result = cast()
        assert len(result.lines) == 6

    def test_lines_are_binary(self) -> None:
        """验证每爻为 0 或 1。"""
        result = cast()
        for line in result.lines:
            assert line in (0, 1)

    def test_changing_lines_in_range(self) -> None:
        """验证变爻索引在有效范围。"""
        for _ in range(50):
            result = cast()
            for pos in result.changing_lines:
                assert 0 <= pos <= 5

    def test_changed_lines_match(self) -> None:
        """验证变卦六爻与变爻位置翻转一致。"""
        for _ in range(50):
            result = cast()
            for i, (orig, changed) in enumerate(
                zip(result.lines, result.changed_lines)
            ):
                if i in result.changing_lines:
                    assert orig != changed
                    assert changed == 1 - orig
                else:
                    assert orig == changed

    def test_has_changing_flag(self) -> None:
        """验证 has_changing 与 changing_lines 一致。"""
        for _ in range(50):
            result = cast()
            assert result.has_changing == (len(result.changing_lines) > 0)

    def test_deterministic_with_seed(self, monkeypatch) -> None:
        """验证固定随机种子下起卦结果一致。"""

        def fixed_choice(seq: list[str]) -> str:
            return seq[0]

        monkeypatch.setattr(random, "choice", fixed_choice)

        result = cast()
        assert result.lines == [1, 1, 1, 1, 1, 1]
        assert result.changing_lines == [0, 1, 2, 3, 4, 5]
        assert result.has_changing is True
        assert result.changed_lines == [0, 0, 0, 0, 0, 0]

    def test_lines_to_binary(self) -> None:
        """验证六爻转二进制编码正确。"""
        assert lines_to_binary([1, 1, 1, 1, 1, 1]) == 63  # 全阳 → 乾
        assert lines_to_binary([0, 0, 0, 0, 0, 0]) == 0   # 全阴 → 坤
        assert lines_to_binary([1, 0, 0, 0, 1, 0]) == 17  # 水雷屯

    def test_lookup_gua_known(self) -> None:
        """验证已知六爻查卦正确。"""
        # 乾为天：全阳
        gua = lookup_gua([1, 1, 1, 1, 1, 1])
        assert gua.index == 1
        assert gua.name == "乾为天"

        # 坤为地：全阴
        gua = lookup_gua([0, 0, 0, 0, 0, 0])
        assert gua.index == 2
        assert gua.name == "坤为地"

        # 水雷屯
        gua = lookup_gua([1, 0, 0, 0, 1, 0])
        assert gua.index == 3
        assert gua.name == "水雷屯"

    def test_lookup_changed_gua(self) -> None:
        """验证变卦查卦正确。"""
        changed = lookup_changed_gua([1, 1, 1, 1, 1, 1])
        assert changed.index == 1
        assert changed.name == "乾为天"

    def test_binary_lookup_all_possible_lines(self) -> None:
        """验证所有 64 种六爻都能正确查卦。"""
        for binary in range(64):
            lines = [(binary >> i) & 1 for i in range(6)]
            gua = lookup_gua(lines)
            assert gua.binary == binary


class TestInterpreter:
    """解卦模块测试。"""

    def test_prompt_with_question(self) -> None:
        """验证有问题的提示词正确生成。"""
        ben = GUA_BY_BINARY[63]  # 乾为天
        changed = GUA_BY_BINARY[0]  # 坤为地

        prompt = build_user_prompt(
            ben_gua=ben,
            question="我该换工作吗？",
            changed_gua=changed,
            changing_lines=[1, 4],
        )

        assert "我该换工作吗？" in prompt
        assert "乾为天" in prompt
        assert "䷀" in prompt
        assert "坤为地" in prompt
        assert "䷁" in prompt
        assert "第2、第5爻" in prompt

    def test_prompt_without_question(self) -> None:
        """验证无问题的提示词正确生成。"""
        ben = GUA_BY_BINARY[63]  # 乾为天
        prompt = build_user_prompt(ben_gua=ben, question=None)

        assert "未说明具体问题" in prompt
        assert "乾为天" in prompt
        assert "请为师解卦" in prompt

    def test_prompt_without_changing_lines(self) -> None:
        """验证无变爻时不包含变卦信息。"""
        ben = GUA_BY_BINARY[63]
        prompt = build_user_prompt(ben_gua=ben, question="测试")

        assert "变卦" not in prompt
        assert "变爻" not in prompt

    def test_system_prompt_exists(self) -> None:
        """验证系统提示词非空。"""
        from interpreter import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 100
        assert "周易" in SYSTEM_PROMPT
        assert "300-500字" in SYSTEM_PROMPT


class TestIntegration:
    """端到端集成测试（不实际调用 API）。"""

    def test_full_flow_no_changing(self, monkeypatch) -> None:
        """验证无变爻的完整流程。"""

        call_index = [0]
        results = ["正面", "正面", "反面"]  # 每爻3+3+2=8（少阴，不变）

        def patched_choice(seq: list[str]) -> str:
            idx = call_index[0] % 3
            call_index[0] += 1
            return results[idx]

        monkeypatch.setattr(random, "choice", patched_choice)

        result = cast()
        gua = lookup_gua(result.lines)

        assert len(result.lines) == 6
        assert gua.index == 2
        assert gua.name == "坤为地"
        assert result.has_changing is False

        prompt = build_user_prompt(ben_gua=gua, question="测试")
        assert "坤为地" in prompt

    def test_full_flow_with_changing(self, monkeypatch) -> None:
        """验证有变爻的完整流程。"""

        def all_heads(seq: list[str]) -> str:
            return "正面"

        monkeypatch.setattr(random, "choice", all_heads)

        result = cast()
        ben = lookup_gua(result.lines)

        assert result.has_changing

        changed = lookup_changed_gua(result.changed_lines)
        assert changed is not None

        prompt = build_user_prompt(
            ben_gua=ben,
            question="测试问题",
            changed_gua=changed,
            changing_lines=result.changing_lines,
        )
        assert "测试问题" in prompt
        assert "变卦" in prompt

    def test_casting_to_prompt_chain(self) -> None:
        """验证起卦→定卦→提示词链路的类型正确性。"""
        result = cast()
        assert isinstance(result, CastingResult)

        ben = lookup_gua(result.lines)
        assert isinstance(ben, GuaInfo)

        prompt = build_user_prompt(
            ben_gua=ben,
            question="端到端测试",
            changed_gua=(
                lookup_changed_gua(result.changed_lines)
                if result.has_changing
                else None
            ),
            changing_lines=(
                result.changing_lines if result.has_changing else None
            ),
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0