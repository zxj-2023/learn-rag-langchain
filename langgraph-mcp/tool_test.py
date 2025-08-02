from langchain_core.tools import tool
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage



# 定义一个加法工具
@tool
def add_numbers(a: float, b: float) -> float:
    """
    Adds two numbers together.

    Args:
        a: The first number.
        b: The second number.
    """
    return a + b

# 我们可以定义更多的工具，例如一个乘法工具
@tool
def multiply_numbers(a: float, b: float) -> float:
    """
    Multiplies two numbers together.

    Args:
        a: The first number.
        b: The second number.
    """
    return a * b

# 将我们定义的工具放在一个列表中
tools = [add_numbers, multiply_numbers]


# 初始化LLM
llm = ChatOpenAI(
    temperature=0.5,
    model_name="deepseek-v3-0324", # 聊天模型通常使用"gpt-3.5-turbo"或"gpt-4"
    openai_api_base="https://api.qnaigc.com/v1", # 例如，您可以指定base_url
    openai_api_key="sk-d1485a93f87c3c0add520ca9a97d507cb810537de27ac5d9a72f2b6ba4651a0d" # 直接在此处设置API密钥，或者通过环境变量设置
)
# 将工具绑定到LLM
# LLM现在知道了add_numbers和multiply_numbers这两个工具及其功能
llm_with_tools = llm.bind_tools(tools)


# 场景一：LLM直接回答，不需要工具
print("--- 场景一：LLM直接回答 ---")
response1 = llm_with_tools.invoke([HumanMessage(content="Hello, what's your name?")])
print(response1.content) # LLM直接生成文本回复

print("\n--- 场景二：LLM决定调用工具 ---")
# 场景二：LLM决定调用工具
# 当LLM的响应中包含tool_calls时，意味着它想要调用一个或多个工具
response2 = llm_with_tools.invoke([HumanMessage(content="What is 15 + 27?")])
print(response2.tool_calls) # 打印LLM决定调用的工具信息

# 检查并执行LLM建议的工具调用
if response2.tool_calls:
    for tool_call in response2.tool_calls:
        if tool_call['name'] == "add_numbers":
            # 提取LLM为工具调用生成的参数
            args = tool_call['args']
            result = add_numbers.invoke(args) # 执行工具
            print(f"Tool call: add_numbers({args['a']}, {args['b']}) = {result}")

            # 将工具的输出发送回LLM，让LLM基于结果生成最终回答
            # 这是一个关键步骤，通常在Agent中自动处理。这里手动演示。
            final_response = llm_with_tools.invoke([
                HumanMessage(content="What is 15 + 27?"),
                AIMessage(content="", tool_calls=[tool_call]), # 告知LLM它之前建议的工具调用
                ToolMessage(content=str(result), tool_call_id=tool_call['id']) # 告知LLM工具的执行结果
            ])
            print("Final LLM response based on tool output:")
            print(final_response.content)

print("\n--- 场景三：另一个工具调用 ---")
response3 = llm_with_tools.invoke([HumanMessage(content="Please multiply 8 by 9.")])
print(response3.tool_calls)

if response3.tool_calls:
    for tool_call in response3.tool_calls:
        if tool_call['name'] == "multiply_numbers":
            args = tool_call['args']
            result = multiply_numbers.invoke(args)
            print(f"Tool call: multiply_numbers({args['a']}, {args['b']}) = {result}")
            final_response = llm_with_tools.invoke([
                HumanMessage(content="Please multiply 8 by 9."),
                AIMessage(content="", tool_calls=[tool_call]),
                ToolMessage(content=str(result), tool_call_id=tool_call['id'])
            ])
            print("Final LLM response based on tool output:")
            print(final_response.content)
