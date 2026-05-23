"""三枚铜钱法算卦 CLI 工具。

用法:
    divination "我最近换工作合适吗？"   # 有问题场景
    divination                          # 无问题场景
"""

import argparse
import json
import os
import sys
from pathlib import Path

from casting import CastingResult, cast, lookup_gua, lookup_changed_gua
from gua_data import GuaInfo
from interpreter import ApiConfig, build_user_prompt, interpret


def _bold(text: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"\033[1m{text}\033[0m"


def _yellow(text: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"\033[33m{text}\033[0m"


def _dim(text: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"\033[2m{text}\033[0m"


def _load_config(config_path: str | None) -> ApiConfig:
    """按优先级查找并加载配置文件。"""
    paths: list[str] = []

    if config_path:
        paths.append(config_path)

    paths.append(str(Path.cwd() / "config.json"))
    paths.append(str(Path.home() / ".divination" / "config.json"))

    for path in paths:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"配置文件 {path} JSON 格式错误: {e}", file=sys.stderr)
                    sys.exit(1)
            return ApiConfig(
                base_url=data.get("base_url", ""),
                api_key=data.get("api_key", ""),
                model=data.get("model", ""),
            )

    print(
        "未找到配置文件。请在当前目录创建 config.json，或放置在 ~/.divination/config.json\n"
        "配置模板：\n"
        '  {\n'
        '    "base_url": "https://api.deepseek.com/v1",\n'
        '    "api_key": "sk-your-api-key",\n'
        '    "model": "deepseek-chat"\n'
        '  }',
        file=sys.stderr,
    )
    sys.exit(1)


def _parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        prog="divination",
        description="三枚铜钱法起卦，调用 AI 进行解卦",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help="求卦问题（可选，不提供时进行通用解卦）",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="API 配置文件路径（默认: 当前目录config.json → ~/.divination/config.json）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="覆写配置中的模型名",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="覆写配置中的 API Key",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="覆写配置中的 API 地址",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="关闭彩色输出",
    )
    return parser.parse_args()


def _validate_config(config: ApiConfig) -> None:
    """验证必填配置项。"""
    missing: list[str] = []
    if not config.base_url:
        missing.append("base_url")
    if not config.api_key:
        missing.append("api_key")
    if missing:
        print(
            f"配置文件缺少必填项: {', '.join(missing)}。"
            "请编辑 config.json 或通过命令行参数指定。",
            file=sys.stderr,
        )
        sys.exit(1)


def _display_gua(
    result: CastingResult,
    ben_gua: GuaInfo,
    changed_gua: GuaInfo | None,
    changing_lines: list[int],
    use_color: bool,
) -> None:
    """输出卦象信息到终端。"""
    width = 40
    print("═" * width)
    print(f"{_bold('本卦', use_color)}: {ben_gua.symbol} {_yellow(ben_gua.name, use_color)}（第{ben_gua.index}卦）")
    print(f"上{ben_gua.upper}下{ben_gua.lower}")
    print(f"卦辞: {ben_gua.summary}")

    if result.has_changing and changed_gua:
        print()
        print(f"{_bold('变卦', use_color)}: {changed_gua.symbol} {_yellow(changed_gua.name, use_color)}（第{changed_gua.index}卦）")
        display_positions = "、".join(f"第{i + 1}" for i in changing_lines)
        print(f"变爻: {display_positions}爻")
    print("═" * width)


def _display_interpretation(text: str, use_color: bool) -> None:
    """输出 AI 解卦内容。"""
    print(f"\n{_bold('解卦', use_color)}")
    print(_dim("─" * 40, use_color))
    print(text)
    print(_dim("─" * 40, use_color))


def main() -> None:
    """CLI 主入口。"""
    args = _parse_args()
    use_color = not args.no_color

    config = _load_config(args.config)

    if args.model:
        config.model = args.model
    if args.api_key:
        config.api_key = args.api_key
    if args.base_url:
        config.base_url = args.base_url

    _validate_config(config)

    result = cast()
    ben_gua = lookup_gua(result.lines)

    changed_gua = None
    if result.has_changing:
        changed_gua = lookup_changed_gua(result.changed_lines)

    _display_gua(result, ben_gua, changed_gua, result.changing_lines, use_color)

    user_prompt = build_user_prompt(
        ben_gua=ben_gua,
        question=args.question,
        changed_gua=changed_gua,
        changing_lines=result.changing_lines if result.has_changing else None,
    )

    print(f"\n{_dim('正在请 AI 师父解卦...', use_color)}\n")

    try:
        interpretation = interpret(config, user_prompt)
    except Exception as e:
        print(f"API 调用失败: {e}", file=sys.stderr)
        sys.exit(1)

    _display_interpretation(interpretation, use_color)


if __name__ == "__main__":
    main()