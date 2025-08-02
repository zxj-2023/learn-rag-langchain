from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# 定义工具
@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

@tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiplies two numbers together."""
    return a * b

tools = [add_numbers, multiply_numbers]

# 初始化LLM
llm = ChatOpenAI(
    temperature=0.5,
    model_name="deepseek-v3-0324", # 聊天模型通常使用"gpt-3.5-turbo"或"gpt-4"
    openai_api_base="https://api.qnaigc.com/v1", # 例如，您可以指定base_url
    openai_api_key="sk-d1485a93f87c3c0add520ca9a97d507cb810537de27ac5d9a72f2b6ba4651a0d" # 直接在此处设置API密钥，或者通过环境变量设置
)

# 将工具绑定到LLM
llm_with_tools = llm.bind_tools(tools)

# llm_with_tools = llm

# 创建Agent
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个乐于助人的AI助手。"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_tool_calling_agent(llm_with_tools, tools, prompt)

# 创建Agent执行器
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 演示对话
chat_history = []

def run_conversation(user_input: str):
    global chat_history
    print(f"\n--- 用户输入: {user_input} ---")
    response = agent_executor.invoke({"input": user_input, "chat_history": chat_history})
    ai_message = AIMessage(content=response["output"])
    chat_history.extend([HumanMessage(content=user_input), ai_message])
    print(f"--- AI 回复: {ai_message.content} ---")

# 场景一：LLM直接回答
run_conversation("你好，你叫什么名字？")

# 场景二：LLM决定调用工具 (加法)
run_conversation("请帮我计算 123 + 456")

# 场景三：LLM决定调用工具 (乘法)
run_conversation("请帮我计算 78 * 90")

# 场景四：多轮对话，结合工具调用和上下文
run_conversation("我叫小明")
run_conversation("我的名字是小明，请问 10 + 20 是多少？")
run_conversation("那 5 * 5 呢？")