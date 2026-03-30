import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from core.config import settings
from core.logger import get_logger
import json

logger = get_logger("services.ai_agent")

class AIAnalysisService:
    def __init__(self):
        # 确保环境变量已设置
        if settings.DASHSCOPE_API_KEY:
            os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY
            
        # 使用通义千问模型 (通过 OpenAI 兼容接口调用 DashScope)
        self.llm = ChatOpenAI(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus", # 使用 qwen-plus 模型，性价比高且能力强
            temperature=0.1    # 较低的温度，保证输出的稳定性
        )
        
        # 定义分析的 Prompt 模板
        self.prompt_template = PromptTemplate(
            input_variables=["news_content"],
            template="""
你是一个资深的金融分析师。请仔细阅读以下抓取到的财经新闻内容，并严格按照要求输出分析结果。

【新闻内容】:
{news_content}

【分析要求】:
请分析这篇新闻对股市（重点是美股或A股）的潜在影响。
必须以 JSON 格式输出，不要包含任何多余的解释或 Markdown 标记。JSON 必须包含以下字段：
1. "summary": 一句话总结事件核心内容（不超过50个字）。
2. "impact_assessment": 对股市或特定公司的影响评估（必须是这三个词之一："利好"、"利空"、"中性"）。
3. "affected_sectors": 受此事件直接或间接影响的行业板块（多个板块用逗号分隔，如"半导体,人工智能"）。
4. "logical_reasoning": 简要推演为什么会产生这种影响的逻辑（100字左右）。

【输出格式】:
{{
  "summary": "...",
  "impact_assessment": "...",
  "affected_sectors": "...",
  "logical_reasoning": "..."
}}
"""
        )
        
        self.chain = self.prompt_template | self.llm

    def analyze_news(self, news_content: str) -> dict:
        """
        调用大模型分析新闻内容
        """
        try:
            # 截取前 8000 个字符，防止超长文本导致 Token 溢出或费用过高
            truncated_content = news_content[:8000]
            
            response = self.chain.invoke({"news_content": truncated_content})
            
            # 清理可能的 Markdown JSON 包裹 (如 ```json ... ```)
            result_text = response.content.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            return json.loads(result_text.strip())
            
        except Exception as e:
            logger.error(f"ai_analysis_error error={str(e)}")
            return {
                "summary": "分析失败",
                "impact_assessment": "中性",
                "affected_sectors": "未知",
                "logical_reasoning": f"调用大模型分析时发生错误: {str(e)}"
            }

# 单例模式
ai_analyzer = AIAnalysisService()
