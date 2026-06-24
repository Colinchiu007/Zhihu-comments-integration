import argparse
from scraper.zhihu_api import ZhihuAPI
from analyzer.comment_analyzer import CommentAnalyzer
from generator.article_generator import ArticleGenerator

def main():
    parser = argparse.ArgumentParser(description='知乎评论整合工具')
    parser.add_argument('--url', required=True, help='知乎链接')
    parser.add_argument('--output', default='output.md', help='输出文件')
    parser.add_argument('--max-comments', type=int, default=50, help='最大评论数')
    
    args = parser.parse_args()
    
    print(f'目标: {args.url}')
    print(f'最大评论数: {args.max_comments}')
    print('='*50)
    
    # 1. 抓取评论
    print('\n[1/3] 抓取评论...')
    api = ZhihuAPI()
    comments = api.scrape(args.url, max_comments=args.max_comments)
    print(f'  抓取到 {len(comments)} 条评论')
    
    if not comments:
        print('未获取到评论，退出')
        return
    
    # 2. 分析评论
    print('\n[2/3] 分析评论...')
    analyzer = CommentAnalyzer()
    analysis = analyzer.analyze(comments)
    print(f'  分析完成: {analysis["summary"][:50]}')
    
    # 3. 生成文章
    print('\n[3/3] 生成文章...')
    generator = ArticleGenerator()
    article = generator.generate(analysis)
    
    # 保存
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(article)
    
    print(f'\n{"="*50}')
    print(f'完成! 文章已保存到: {args.output}')
    print(f'评论数: {len(comments)}')

if __name__ == '__main__':
    main()
