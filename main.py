import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.zhihu_api import ZhihuAPI
from analyzer.comment_analyzer import CommentAnalyzer
from generator.article_generator import ArticleGenerator
from rewriter.comment_rewriter import CommentRewriter, RewriteConfig
from data.storage import DataStorage


def sanitize_filename(title: str) -> str:
    """清理文件名中的非法字符"""
    # 移除或替换非法字符
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # 限制长度
    if len(title) > 50:
        title = title[:50]
    return title.strip()


def main():
    parser = argparse.ArgumentParser(description='知乎评论整合工具')
    parser.add_argument('--url', required=True, help='知乎链接')
    parser.add_argument('--output', default=None, help='分析报告输出文件（默认：标题-日期.md）')
    parser.add_argument('--max-comments', type=int, default=50, help='最大评论数')
    parser.add_argument('--rewrite', action='store_true', help='生成改写文案')
    parser.add_argument('--rewrite-output', default=None, help='改写文案输出文件（默认：标题-日期.md）')
    parser.add_argument('--max-words', type=int, default=2000, help='改写文案最大字数')
    parser.add_argument('--strategy', choices=['auto', '评论为主', '原文为主', '均衡'], 
                       default='auto', help='改写策略')
    parser.add_argument('--max-duplicate-ratio', type=float, default=0.5, 
                       help='与原文最大重复率（0-1，默认0.5）')
    parser.add_argument('--save', action='store_true', help='保存原文和评论到文件')
    parser.add_argument('--data-dir', default='data', help='数据保存目录')
    
    args = parser.parse_args()
    
    print(f'目标: {args.url}')
    print(f'最大评论数: {args.max_comments}')
    if args.rewrite:
        print(f'改写策略: {args.strategy}')
        print(f'改写字数上限: {args.max_words}')
        print(f'与原文最大重复率: {args.max_duplicate_ratio:.0%}')
    if args.save:
        print(f'数据保存目录: {args.data_dir}')
    print('='*50)
    
    # 1. 抓取内容
    print('\n[1/5] 抓取内容...')
    api = ZhihuAPI()
    data = api.scrape(args.url, max_comments=args.max_comments, include_original=args.save)
    comments = data.get('comments', [])
    print(f'  抓取到 {len(comments)} 条评论')
    
    if args.save and data.get('original'):
        print(f'  已获取原文: {data["original"].get("question_title", "")[:30]}...')
    
    if not comments:
        print('未获取到评论，退出')
        return
    
    # 2. 分析评论
    print('\n[2/5] 分析评论...')
    analyzer = CommentAnalyzer()
    analysis = analyzer.analyze(comments)
    print(f'  分析完成: {analysis["summary"][:50]}')
    
    # 从原文或分析中获取标题
    title = '知乎讨论'
    if data.get('original'):
        title = data['original'].get('question_title', title)
    analysis['title'] = title
    
    # 生成文件名
    date_str = datetime.now().strftime('%Y%m%d')
    safe_title = sanitize_filename(title)
    default_filename = f'{safe_title}-{date_str}.md'
    
    # 3. 生成分析报告
    print('\n[3/5] 生成分析报告...')
    generator = ArticleGenerator()
    article = generator.generate(analysis)
    
    output_file = args.output or default_filename
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(article)
    print(f'  分析报告已保存: {output_file}')
    
    # 4. 生成改写文案（可选）
    if args.rewrite:
        print('\n[4/5] 生成改写文案...')
        config = RewriteConfig(
            max_words=args.max_words,
            strategy=args.strategy,
            max_duplicate_ratio=args.max_duplicate_ratio
        )
        rewriter = CommentRewriter(config)
        
        # 获取原文内容
        original = ''
        if data.get('original'):
            original = data['original'].get('content', '')
        
        rewritten = rewriter.rewrite(original, comments, analysis)
        
        rewrite_file = args.rewrite_output or f'改写-{default_filename}'
        with open(rewrite_file, 'w', encoding='utf-8') as f:
            f.write(rewritten)
        print(f'  改写文案已保存: {rewrite_file}')
    else:
        print('\n[4/5] 跳过改写文案（使用 --rewrite 启用）')
    
    # 5. 保存数据（可选）
    if args.save:
        print('\n[5/5] 保存数据...')
        storage = DataStorage(args.data_dir)
        file_path = storage.save_answer(data)
        print(f'  数据已保存: {file_path}')
        
        # 显示统计
        stats = storage.get_statistics()
        print(f'  存储统计: {stats["total_answers"]}条回答, {stats["total_comments"]}条评论')
    else:
        print('\n[5/5] 跳过数据保存（使用 --save 启用）')
    
    print(f'\n{"="*50}')
    print(f'完成!')
    print(f'  - 分析报告: {output_file}')
    if args.rewrite:
        print(f'  - 改写文案: {rewrite_file}')
    if args.save:
        print(f'  - 数据目录: {args.data_dir}')


if __name__ == '__main__':
    main()
