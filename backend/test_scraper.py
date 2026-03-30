import sys
import os

# 将 backend 目录添加到 sys.path 中，以便可以导入 services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scraper import jina_reader

def test_scraper():
    # 换一篇确实存在的长文（比如维基百科或GitHub的说明）来验证解析效果
    test_url = "https://en.wikipedia.org/wiki/Stock_market"
    print(f"正在使用 Jina Reader 抓取 URL: {test_url} ...")
    print("请稍等，可能需要几秒钟...")
    
    markdown_content = jina_reader.fetch_markdown(test_url)
    
    if markdown_content:
        print("\n" + "="*50)
        print("抓取成功！以下是提取出的 Markdown 格式正文（前 500 个字符）：")
        print("="*50 + "\n")
        print(markdown_content[:500] + "\n...\n(内容过长已截断)")
    else:
        print("抓取失败，请检查网络或 URL。")

if __name__ == "__main__":
    test_scraper()