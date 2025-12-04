"""Studio 的 SQL 代理。"""

import pathlib
import re

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

llm = init_chat_model("openai:gpt-5")

# 获取数据库并保存在本地

url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
local_path = pathlib.Path("Chinook.db")

if local_path.exists():
    print(f"{local_path} already exists, skipping download.")
else:
    response = requests.get(url)
    if response.status_code == 200:
        local_path.write_bytes(response.content)
        print(f"File downloaded and saved as {local_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

# print(f"Dialect: {db.dialect}")
# print(f"Available tables: {db.get_usable_table_names()}")
# print(f'Sample output: {db.run("SELECT * FROM Artist LIMIT 5;")}')

SCHEMA = db.get_table_info()

DENY_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|REPLACE|TRUNCATE)\b", re.I
)
HAS_LIMIT_TAIL_RE = re.compile(r"(?is)\blimit\b\s+\d+(\s*,\s*\d+)?\s*;?\s*$")


def _safe_sql(q: str) -> str:
    # 规范化输入
    q = q.strip()
    # 阻止多条语句（只允许可选的末尾分号）
    if q.count(";") > 1 or (q.endswith(";") and ";" in q[:-1]):
        return "Error: multiple statements are not allowed."
    q = q.rstrip(";").strip()

    # 只允许只读查询
    if not q.lower().startswith("select"):
        return "Error: only SELECT statements are allowed."
    if DENY_RE.search(q):
        return "Error: DML/DDL detected. Only read-only queries are permitted."

    # 如果末尾没有 LIMIT，则追加（对空白/换行做了兼容）
    if not HAS_LIMIT_TAIL_RE.search(q):
        q += " LIMIT 5"
    return q


@tool
def execute_sql(query: str) -> str:
    """执行只读的 SQLite SELECT 查询并返回结果。"""
    query = _safe_sql(query)
    q = query
    if q.startswith("Error:"):
        return q
    try:
        return db.run(q)
    except Exception as e:
        return f"Error: {e}"


SYSTEM_PROMPT = f"""You are a careful SQLite analyst.

Authoritative schema (do not invent columns/tables):
{SCHEMA}

Rules:
- Think step-by-step.
- When you need data, call the tool `execute_sql` with ONE SELECT query.
- Read-only only; no INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.
- Limit to 5 rows unless user explicitly asks otherwise.
- If the tool returns 'Error:', revise the SQL and try again.
- Limit the number of attempts to 5. 
- If you are not successful after 5 attempts, return a note to the user.
- Prefer explicit column lists; avoid SELECT *.
"""


agent = create_agent(
    model=llm,
    tools=[execute_sql],
    system_prompt=SYSTEM_PROMPT,
)

# 示例：
# question = "Which genre on average has the longest tracks?"
# for step in agent.stream({"messages": [{"role":"user","content": question}]}, stream_mode="values"):
#    step["messages"][-1].pretty_print()
