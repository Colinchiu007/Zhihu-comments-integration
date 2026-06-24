from typing import Dict, Any, List
from datetime import datetime

class ArticleGenerator:
    def __init__(self):
        self.template = """# 知乎评论分析报告

**生成时间**: {timestamp}

## 概述

{summary}

## 核心关键词

{keywords_section}

## 情感分布

- **积极评论**: {positive_count}条 ({positive_ratio:.1%})
- **消极评论**: {negative_count}条 ({negative_ratio:.1%})
- **整体情感值**: {avg_sentiment:.2%}

## 主要观点

### 正面观点

{positive_points}

### 负面观点

{negative_points}

## 热门讨论

{hot_topics}

## 总结

{conclusion}

---

*本报告基于{total_comments}条自动生成，仅供参考。*
"""
    
    def _format_keywords(self, keywords: List[str]) -> str:
        if not keywords:
            return "暂无关键词"
        return "、".join(keywords[:10])
    
    def _format_points(self, comments: List[Dict[str, Any]], top_n: int = 5) -> str:
        if not comments:
            return "暂无相关评论"
        
        points = []
        for i, comment in enumerate(comments[:top_n], 1):
            content = comment.get('content', '')[:100] + "..." if len(comment.get('content', '')) > 100 else comment.get('content', '')
            author = comment.get('author', '匿名用户')
            points.append(f"{i}. **{author}**: {content}")
        
        return "\n".join(points)
    
    def _generate_hot_topics(self, word_freq: List[tuple]) -> str:
        if not word_freq:
            return "暂无热门话题"
        
        topics = []
        for word, freq in word_freq[:8]:
            topics.append(f"- **{word}**: {freq}次")
        
        return "\n".join(topics)
    
    def _generate_conclusion(self, analysis: Dict[str, Any]) -> str:
        stats = analysis.get('stats', {})
        positive_count = len(analysis.get('positive_comments', []))
        negative_count = len(analysis.get('negative_comments', []))
        
        if positive_count > negative_count * 2:
            return "整体舆论偏向正面，用户对该话题持肯定态度。"
        elif negative_count > positive_count * 2:
            return "整体舆论偏向负面，用户对该话题存在较多争议。"
        else:
            return "舆论观点多元，存在不同声音，建议理性看待。"
    
    def generate(self, analysis: Dict[str, Any]) -> str:
        if 'error' in analysis:
            return f"# 错误\n\n{analysis['error']}"
        
        stats = analysis.get('stats', {})
        
        template_vars = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': analysis.get('summary', '暂无摘要'),
            'keywords_section': self._format_keywords(stats.get('keywords', [])),
            'positive_count': len(analysis.get('positive_comments', [])),
            'negative_count': len(analysis.get('negative_comments', [])),
            'positive_ratio': stats.get('positive_ratio', 0),
            'negative_ratio': stats.get('negative_ratio', 0),
            'avg_sentiment': stats.get('avg_sentiment', 0.5),
            'positive_points': self._format_points(analysis.get('positive_comments', [])),
            'negative_points': self._format_points(analysis.get('negative_comments', [])),
            'hot_topics': self._generate_hot_topics(stats.get('word_freq', [])),
            'total_comments': stats.get('total_comments', 0),
            'conclusion': self._generate_conclusion(analysis)
        }
        
        return self.template.format(**template_vars)