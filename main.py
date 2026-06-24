import argparse
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.zhihu_api import ZhihuAPI
from analyzer.comment_analyzer import CommentAnalyzer
from generator.article_generator import ArticleGenerator
from rewriter.comment_rewriter import CommentRewriter, RewriteConfig


def main():
    parser = argparse.ArgumentParser(description='知乎评论整合工具')
    parser.add_argument('--url', required=True, help='知乎链接')
    parser.add_argument('--output', default='output.md', help='分析报告输出文件')
    parser.add_argument('--max-comments', type=int, default=50, help='最大评论数')
    parser.add_argument('--rewrite', action='store_true', help='生成改写文案')
    parser.add_argument('--rewrite-output', default='rewritten.md', help='改写文案输出文件')
    parser.add_argument('--max-words', type=int, default=2000, help='改写文案最大字数')
    parser.add_argument('--strategy', choices=['auto', '评论为主', '原文为主', '均衡'], 
                       default='auto', help='改写策略')
    
    args = parser.parse_args()
    
    print(f'目标: {args.url}')
    print(f'最大评论数: {args.max_comments}')
    if args.rewrite:
        print(f'改写策略: {args.strategy}')
        print(f'改写字数上限: {args.max_words}')
    print('='*50)
    
    # 1. 抓取评论
    print('\n[1/4] 抓取评论...')
    api = ZhihuAPI()
    comments = api.scrape(args.url, max_comments=args.max_comments)
    print(f'  抓取到 {len(comments)} 条评论')
    
    if not comments:
        print('未获取到评论，退出')
        return
    
    # 2. 分析评论
    print('\n[2/4] 分析评论...')
    analyzer = CommentAnalyzer()
    analysis = analyzer.analyze(comments)
    print(f'  分析完成: {analysis["summary"][:50]}')
    
    # 3. 生成分析报告
    print('\n[3/4] 生成分析报告...')
    generator = ArticleGenerator()
    article = generator.generate(analysis)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(article)
    print(f'  分析报告已保存: {args.output}')
    
    # 4. 生成改写文案（可选）
    if args.rewrite:
        print('\n[4/4] 生成改写文案...')
        config = RewriteConfig(
            max_words=args.max_words,
            strategy=args.strategy
        )
        rewriter = CommentRewriter(config)
        
        # 获取原文（从API响应中）
        original = ''  # TODO: 从API获取原文
        
        rewritten = rewriter.rewrite(original, comments, analysis)
        
        with open(args.rewrite_output, 'w', encoding='utf-8') as f:
            f.write(rewritten)
        print(f'  改写文案已保存: {args.rewrite_output}')
    else:
        print('\n[4/4] 跳过改写文案（使用 --rewrite 启用）')
    
    print(f'\n{"="*50}')
    print(f'完成!')
    print(f'  - 分析报告: {args.output}')
    if args.rewrite:
        print(f'  - 改写文案: {args.rewrite_output}')


if __name__ == '__main__':
    main()
