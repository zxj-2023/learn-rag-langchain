# env_utils.py
import os
from dotenv import dotenv_values

def summarize_value(value: str) -> str:
    """返回掩码形式：****后四位，或布尔字符串。"""
    lower = value.lower()
    if lower in ("true", "false"):
        return lower
    return "****" + value[-4:] if len(value) > 4 else "****" + value

def doublecheck_env(file_path: str):
    """将环境变量与 .env 文件比对，并打印摘要。"""
    if not os.path.exists(file_path):
        print(f"未找到文件 {file_path}。")
        print("此脚本用于再次核对 notebook 的关键配置。")
        print("这只是检查步骤，并非必需。\n")
        return

    parsed = dotenv_values(file_path)
    for key in parsed.keys():
        current = os.getenv(key)
        if current is not None:
            print(f"{key}={summarize_value(current)}")
        else:
            print(f"{key}=<未设置>")




# ========== 基于 pyproject.toml 检查 Python 及依赖的小工具  =====================================

# 依赖：pip install packaging
import sys, tomllib
from pathlib import Path
from importlib import metadata
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

def _fmt_row(cols, widths):
    return " | ".join(str(c).ljust(w) for c, w in zip(cols, widths))

def doublecheck_pkgs(pyproject_path="pyproject.toml", verbose=False):
    p = Path(pyproject_path)
    if not p.exists():
        print(f"错误：未找到 {pyproject_path}。")
        return None

    # 读取 pyproject 以及 Python 版本要求
    with p.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    python_spec_str = project.get("requires-python") or ">=3.11"

    py_ver = Version(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    py_ok = py_ver in SpecifierSet(python_spec_str)

    # 读取依赖（PEP 621）
    deps = project.get("dependencies", [])
    if not deps:
        if verbose or not py_ok:
            print("pyproject.toml 中没有 [project].dependencies。")
            print(f"Python {py_ver} {'满足' if py_ok else '不满足'} requires-python: {python_spec_str}")
            print(f"可执行文件：{sys.executable}")
        return None

    # 评估依赖
    results = []
    problems = []
    for dep in deps:
        try:
            req = Requirement(dep)
            name = req.name
            spec = str(req.specifier) if req.specifier else "(any)"
        except Exception:
            name, spec = dep, "(unparsed)"

        rec = {"package": name, "required": spec, "installed": "-", "path": "-", "status": "❌ 缺失"}

        try:
            installed_ver = metadata.version(name)
            rec["installed"] = installed_ver
            try:
                dist = metadata.distribution(name)
                rec["path"] = str(dist.locate_file(""))
            except Exception:
                rec["path"] = "(未知)"

            if spec not in ("(any)", "(unparsed)") and any(op in spec for op in "<>="):
                sset = SpecifierSet(spec)
                if Version(installed_ver) in sset:
                    rec["status"] = "✅ 正常"
                else:
                    rec["status"] = "⚠️ 版本不匹配"
            else:
                rec["status"] = "✅ 正常"

        except metadata.PackageNotFoundError:
            # 保持默认值：installed "-"，status "❌ 缺失"
            pass

        results.append(rec)
        if rec["status"] != "✅ 正常":
            problems.append(rec)

    should_print = verbose or (not py_ok) or bool(problems)
    if should_print:
        # Python 状态
        print(f"Python {py_ver} {'满足' if py_ok else '不满足'} requires-python: {python_spec_str}")

        # 表格（无提示列）
        headers = ["包", "要求", "已安装", "状态", "路径"]
        def short_path(s, maxlen=80):
            s = str(s)
            return s if len(s) <= maxlen else ("..." + s[-(maxlen-3):])
        rows = [[r["package"], r["required"], r["installed"], r["status"], short_path(r["path"])] for r in results]
        widths = [max(len(h), *(len(str(row[i])) for row in rows)) for i, h in enumerate(headers)]
        print(_fmt_row(headers, widths))
        print(_fmt_row(["-"*w for w in widths], widths))
        for row in rows:
            print(_fmt_row(row, widths))

        # 总结问题，但不指定修复工具
        if problems:
            print("\n检测到的问题：")
            for r in problems:
                print(f"- {r['package']}: {r['status']} (要求 {r['required']}，已安装 {r['installed']}，路径 {r['path']})")

        if verbose or problems or not py_ok:
            print("\n环境：")
            print(f"- 可执行文件：{sys.executable}")

    return None
