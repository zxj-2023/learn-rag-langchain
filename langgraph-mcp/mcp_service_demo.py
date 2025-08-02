import os
import asyncio
from getpass import getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

# 定义MCP服务器配置
mcp_servers_config = {
    "fetch": {
        "transport": "sse",
        "url": "https://mcp.api-inference.modelscope.net/a30b4276b9cc40/sse",
        "headers": {},
    }
}

async def main():
    # 初始化LLM
    llm = ChatOpenAI(
        temperature=0,
        model="deepseek-v3-0324", 
        openai_api_base="https://api.qnaigc.com/v1", # 例如，您可以指定base_url
        openai_api_key="sk-d1485a93f87c3c0add520ca9a97d507cb810537de27ac5d9a72f2b6ba4651a0d" # 直接在此处设置API密钥，或者通过环境变量设置
    )

    # 初始化MCP客户端并获取工具
    print("\n--- 初始化MCP客户端并获取工具 ---")
    client = MultiServerMCPClient(mcp_servers_config)
    try:
        tools = await client.get_tools()
        print(f"成功获取到 {len(tools)} 个MCP工具。")
        for tool_item in tools:
            print(f"  - {tool_item.name}: {tool_item.description}")
    except Exception as e:
        print(f"获取MCP工具失败: {e}")
        print("请确保MCP服务URL有效且可访问，或者您已正确配置了认证信息。")
        return

    # 将MCP工具绑定到LLM
    # 这使得LLM知道如何调用MCP服务
    llm_with_tools = llm.bind_tools(tools)

    print("\n--- 演示1: LLM尝试调用MCP服务 ---")

    query = "给我调查一下 https://helloworld.openeee.cn 这个网址的信息"

    # 直接调用LLM，它会尝试生成工具调用
    response = llm_with_tools.invoke(query)
    print(f"LLM Response (potential tool call): {response}")

    # 检查LLM是否生成了工具调用
    if response.tool_calls:
        print("LLM generated tool calls:")
        for tool_call in response.tool_calls:
            print(f"  Tool Name: {tool_call['name']}")
        print(f"  Tool Args: {tool_call['args']}")
        print(f"  Tool ID: {tool_call['id']}")
    else:
        print("LLM did not generate any tool calls for this query.")

    print("\n--- 演示2: 结合AgentExecutor进行MCP服务调用 (概念性演示) ---")

    # 创建Agent的Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant that can query MCP specifications."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 创建Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    #print("演示agent")
    #agent.invoke(({"input": query}))
    # 创建AgentExecutor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 运行AgentExecutor来调用MCP服务
    try:
        agent_response = await agent_executor.ainvoke({"input": query})
        print(f"Agent Executor Response: {agent_response['output']}")
    except Exception as e:
        print(f"Error running Agent Executor (expected if no real MCP service): {e}")

if __name__ == "__main__":
    asyncio.run(main())