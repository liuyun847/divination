"""解卦模块。

构建提示词并调用 OpenAI 兼容接口进行 AI 解卦。
"""

from dataclasses import dataclass

from gua_data import GuaInfo

SYSTEM_PROMPT = """\
你是一位精通《周易》的算命师父，擅长结合卦象为求卦者答疑解惑。
解读时请：
1. 先介绍本卦的核心含义和吉凶
2. 如有变卦，说明变卦对整体趋势的影响
3. 若求卦者有问题，结合问题给出针对性的建议
4. 若求卦者没有问题，给出此卦通用的劝诫和启示
5. 语言通俗但不失深度，控制在300-500字\
"""


@dataclass
class ApiConfig:
    """API 配置。"""

    base_url: str
    api_key: str
    model: str


def _format_changing_lines(changing_lines: list[int]) -> str:
    """格式化变爻位置字符串，如 '第2、第5爻'。"""
    display = [str(i + 1) for i in changing_lines]
    return "、".join(f"第{d}" for d in display) + "爻"


def build_user_prompt(
    ben_gua: GuaInfo,
    question: str | None = None,
    changed_gua: GuaInfo | None = None,
    changing_lines: list[int] | None = None,
) -> str:
    """构建用户提示词。"""
    parts: list[str] = []

    if question:
        parts.append(f"求卦者问题：{question}")
        parts.append("")
    else:
        parts.append("求卦者前来问卦，未说明具体问题。")
        parts.append("")

    parts.append(f"本卦：第{ben_gua.index}卦 {ben_gua.name}（{ben_gua.symbol}）")
    parts.append(f"上{ben_gua.upper}下{ben_gua.lower}")
    parts.append(f"卦辞概要：{ben_gua.summary}")

    if changed_gua and changing_lines:
        parts.append("")
        changed_str = _format_changing_lines(changing_lines)
        parts.append(f"变卦：第{changed_gua.index}卦 {changed_gua.name}（{changed_gua.symbol}）")
        parts.append(f"变爻位置：{changed_str}")

    parts.append("")
    parts.append("请为师解卦")
    return "\n".join(parts)


def interpret(
    config: ApiConfig,
    user_prompt: str,
) -> str:
    """调用 AI API 解卦，返回解读文本。"""
    from openai import OpenAI

    client = OpenAI(base_url=config.base_url, api_key=config.api_key)
    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content
    if content is None:
        return "（AI 未返回解读内容，请重试）"
    return content


__all__ = ["ApiConfig", "SYSTEM_PROMPT", "build_user_prompt", "interpret"]