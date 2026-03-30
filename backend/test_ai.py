import sys
import os

# 将 backend 目录添加到 sys.path 中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_agent import ai_analyzer

def test_ai_analysis():
    # 检查环境变量是否已加载
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("警告：未在环境变量中找到 DASHSCOPE_API_KEY，这可能会导致调用失败！")
        print("请确保你已经在电脑环境变量中配置了 DASHSCOPE_API_KEY")
    else:
        print(f"已检测到 API Key (前缀): {api_key[:5]}...")

    # 一段模拟的测试新闻文本
    test_news = """
    美东时间周四，美国商务部宣布对向中国出口特定高端人工智能芯片的限制进行部分豁免。
    文件指出，某些用于医疗研究和气候建模的AI芯片将被允许继续销售。
    消息一出，英伟达（Nvidia）股价在盘后交易中大涨 4.5%，AMD 同样跟涨 3.2%。
    分析人士认为，这可能标志着中美在科技领域的紧张关系出现阶段性缓和。
    """
    
    print("\n" + "="*50)
    print("正在调用通义千问大模型进行分析，请稍候...")
    print("="*50 + "\n")
    
    result = ai_analyzer.analyze_news(test_news)
    
    print("【AI 分析结果】")
    print(f"1. 事件摘要: {result.get('summary')}")
    print(f"2. 影响评估: {result.get('impact_assessment')}")
    print(f"3. 影响板块: {result.get('affected_sectors')}")
    print(f"4. 逻辑推演: {result.get('logical_reasoning')}")

if __name__ == "__main__":
    test_ai_analysis()