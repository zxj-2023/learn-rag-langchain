from langgraph_supervisor import create_supervisor
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from typing import Annotated
from langgraph.prebuilt import InjectedState, create_react_agent
from langchain_openai import ChatOpenAI
import matplotlib.pyplot as plt
import io

# 初始化模型
llm = ChatOpenAI(
    model="qwen3-235b-a22b-thinking-2507",
    api_key="sk-081025394d9e4f35adbb67ea07c3dae1",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 1. 定义研究团队的代理
@tool
def web_search(query: str) -> str:
    """执行网络搜索"""
    return f"搜索结果：关于'{query}'的最新信息..."

@tool
def analyze_data(data: str) -> str:
    """分析数据"""
    return f"数据分析结果：{data}的趋势显示..."

research_agent = create_react_agent(
    model=llm,
    tools=[web_search, analyze_data],
    prompt="你是一个研究专家，负责进行网络搜索和数据分析。",
    name="research_specialist"
)

# 2. 定义数学团队的代理
@tool
def calculate_statistics(numbers: list[float]) -> str:
    """计算统计值"""
    if not numbers:
        return "错误：数据列表为空"
    avg = sum(numbers) / len(numbers)
    return f"统计结果：平均值={avg:.2f}，数据点数量={len(numbers)}"

@tool
def solve_equation(equation: str) -> str:
    """解方程"""
    return f"方程 {equation} 的解为：x = 42"

math_agent = create_react_agent(
    model=llm,
    tools=[calculate_statistics, solve_equation],
    prompt="你是一个数学专家，负责统计计算和方程求解。",
    name="math_specialist"
)

# 3. 创建研究团队主管
research_supervisor = create_supervisor(
    model=llm,
    agents=[research_agent],
    prompt=(
        "你是研究团队的主管。\n"
        "你的团队有一个研究专家，负责网络搜索和数据分析。\n"
        "根据任务需求，将工作分配给研究专家。\n"
        "等待专家完成任务后，总结结果并报告给上级主管。"
    ),
    name="research_supervisor"
).compile(name="research_supervisor")

# 4. 创建数学团队主管
math_supervisor = create_supervisor(
    model=llm,
    agents=[math_agent],
    prompt=(
        "你是数学团队的主管。\n"
        "你的团队有一个数学专家，负责统计计算和方程求解。\n"
        "根据任务需求，将工作分配给数学专家。\n"
        "等待专家完成任务后，总结结果并报告给上级主管。"
    ),
    name="math_supervisor"
).compile(name="math_supervisor")

# 5. 创建顶层主管
top_supervisor = create_supervisor(
    model=llm,
    agents=[research_supervisor, math_supervisor],
    prompt=(
        "你是顶层主管，管理两个专业团队：\n"
        "- 研究团队：负责市场调研、数据分析等任务\n"
        "- 数学团队：负责统计计算、方程求解等任务\n"
        "根据任务的性质，将工作分配给相应的团队主管。\n"
        "等待团队完成任务后，整合所有结果并给出最终报告。"
    ),
    name="top_supervisor"
).compile(name="top_supervisor")

# 可视化并保存图
def visualize_and_save_graph(graph, filename="multi_agent_graph.png"):
    """
    可视化并保存编译后的图
    
    Args:
        graph: 编译后的图对象
        filename: 保存的文件名
    """
    try:
        # 方法1: 使用get_graph().draw_mermaid_png() (如果支持)
        try:
            from PIL import Image
            import io
            
            # 生成mermaid图
            mermaid_graph = graph.get_graph().draw_mermaid_png()
            
            # 保存图片
            image = Image.open(io.BytesIO(mermaid_graph))
            image.save(filename)
            print(f"图表已保存为 {filename}")
            return True
        except Exception as e:
            print(f"使用mermaid可视化失败: {e}")
        
        # 方法2: 使用draw方法 (如果支持)
        try:
            # 尝试生成图形表示
            graph_image = graph.get_graph().draw_ascii()
            print("ASCII图形表示:")
            print(graph_image)
            
            # 保存ASCII图形到文件
            with open(filename.replace('.png', '.txt'), 'w', encoding='utf-8') as f:
                f.write(graph_image)
            print(f"ASCII图表已保存为 {filename.replace('.png', '.txt')}")
            return True
        except Exception as e:
            print(f"使用ASCII可视化失败: {e}")
            
        # 方法3: 手动生成节点和边的信息
        try:
            graph_info = graph.get_graph()
            nodes = [node for node in graph_info.nodes]
            edges = [(edge.source, edge.target) for edge in graph_info.edges]
            
            print("图结构信息:")
            print(f"节点: {nodes}")
            print(f"边: {edges}")
            
            # 保存图结构信息到文件
            with open(f"graph_structure_{filename.replace('.png', '.txt')}", 'w', encoding='utf-8') as f:
                f.write("节点列表:\n")
                for node in nodes:
                    f.write(f"  - {node}\n")
                f.write("\n边列表:\n")
                for source, target in edges:
                    f.write(f"  - {source} -> {target}\n")
            print(f"图结构信息已保存为 graph_structure_{filename.replace('.png', '.txt')}")
            return True
            
        except Exception as e:
            print(f"获取图结构信息失败: {e}")
            
        return False
        
    except Exception as e:
        print(f"可视化过程中出现错误: {e}")
        return False

# 运行可视化
if __name__ == "__main__":
    print("正在生成多代理系统图的可视化...")
    
    # 可视化顶层主管图
    success = visualize_and_save_graph(top_supervisor, "hierarchical_agent_system.png")
    
    if success:
        print("可视化完成!")
    else:
        print("可视化失败，请检查您的环境是否支持图形生成。")
    
    # 运行一个简单的测试任务
    print("\n=== 测试任务 ===")
    try:
        result = top_supervisor.invoke({
            "messages": [HumanMessage(content="请计算以下数据的统计值：[10, 20, 30, 40, 50]")]
        })
        print("测试结果：", result["messages"][-1].content)
    except Exception as e:
        print(f"测试任务执行失败: {e}")