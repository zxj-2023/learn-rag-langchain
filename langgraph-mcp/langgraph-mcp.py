# /workspace/test.py

import asyncio # 需要导入 asyncio 来运行异步函数
# 从langchain_mcp_adapters.client模块导入MultiServerMCPClient类
# 从langgraph.prebuilt模块导入create_react_agent函数
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# 导入 LLM 相关库
from langchain_openai import ChatOpenAI

# 将主要逻辑封装在一个异步函数中
async def main():
    # 创建MultiServerMCPClient实例，配置两个不同的服务
    client = MultiServerMCPClient(
        {
            "math": {  # 数学计算服务
                "command": "python",  # 使用python命令启动
                # 替换为你的math_server.py文件的绝对路径
                "args": ["/workspace/langgraph-mcp/math_server.py"],
                "transport": "stdio",  # 使用标准输入输出传输
            },
            "weather": {  # 天气服务
                # 确保你的天气服务器在8000端口运行
                # *** 确保这个 URL 是正确的，并且服务器正在运行 ***
                "url": "http://localhost:8000/mcp",
                "transport": "streamable_http",  # 使用可流式HTTP传输
            }
        }
    )

    tools = []
    try:
        # 在异步函数内部正确使用 await
        tools = await client.get_tools()
        print(f"成功获取到 {len(tools)} 个MCP工具。")
        for tool_item in tools:
            print(f"  - {tool_item.name}: {tool_item.description}")
    except Exception as e:
        print(f"获取MCP工具失败: {e}")
        print("请确保MCP服务URL有效且可访问，或者您已正确配置了认证信息。")
        # 在函数内部，如果出错可以选择返回或继续处理
        # return # 这里可以 return，但会结束 main 函数

    if not tools:
        print("没有获取到工具，无法创建代理。")
        return

    # 创建ReAct代理
    llm = ChatOpenAI(
        model="qwen3-235b-a22b-thinking-2507",
        api_key="sk-a8ef27c47ea84224ac6eed6d4bba1bab",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1" # 修正了末尾多余的空格
    )
    agent = create_react_agent(llm, tools)
    

    # 异步调用代理来解决数学问题
    # 确保在异步函数内部使用 await
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    print("\n--- 数学问题回答 ---")
    print(math_response["messages"][-1].content) # 打印最后一条消息（LLM的回答）

    # 异步调用代理来查询天气
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
    print("\n--- 天气问题回答 ---")
    print(weather_response["messages"][-1].content) # 打印最后一条消息（LLM的回答）


# --- 这是脚本的入口点 ---
# 使用 asyncio.run() 来运行你的主异步函数
if __name__ == "__main__":
    asyncio.run(main())
