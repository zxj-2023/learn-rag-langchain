"""Studio 的 SQL 代理。"""

import pathlib
import re

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from dotenv import load_dotenv

# 从 .env 加载环境变量
load_dotenv()
from langchain_qwq import ChatQwen
import os
llm=ChatQwen(
    model="qwen3-max",
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

# 数据库来源：
# url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

@tool
def execute_sql(query: str) -> str:
    """执行查询并返回结果。"""

    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"


SYSTEM_PROMPT = """You are a careful SQLite analyst.

Rules:
- Think step-by-step.
- When you need data, call the tool `execute_sql` with ONE SELECT query.
- Read-only only; no INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.
- Limit to 5 rows of output unless the user explicitly asks otherwise.
- If the tool returns 'Error:', revise the SQL and try again.
- Prefer explicit column lists; avoid SELECT *.
"""
# 目前 studio 还不支持传入运行时上下文

agent = create_agent(
    model=llm,
    tools=[execute_sql],
    system_prompt=SYSTEM_PROMPT,
)

# 示例：
# question = "Which genre on average has the longest tracks?"
# for step in agent.stream({"messages": [{"role":"user","content": question}]}, stream_mode="values"):
#    step["messages"][-1].pretty_print()
