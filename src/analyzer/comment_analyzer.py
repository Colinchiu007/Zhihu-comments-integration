import jieba
import jieba.analyse
from snownlp import SnowNLP
from typing import List, Dict, Any
from collections import Counter

class CommentAnalyzer:
    def __init__(self):
        self.stopwords = set()
        self._load_stopwords()
    
    def _load_stopwords(self):
        try:
            with open('config/stopwords.txt', 'r', encoding='utf-8') as f:
                self.stopwords = set([line.strip() for line in f])
        except FileNotFoundError:
            self.stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    def _clean_html(self, text: str) -> str:
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
    def _analyze_sentiment(self, text: str) -> float:
        try:
            clean_text = self._clean_html(text)
            s = SnowNLP(clean_text)
            return s.sentiments
        except:
            return 0.5
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        clean_text = self._clean_html(text)
        keywords = jieba.analyse.extract_tags(clean_text, topK=top_k, withWeight=False)
        return [kw for kw in keywords if kw not in self.stopwords and len(kw) > 1]
    
    def _calculate_stats(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        contents = [c['content'] for c in comments if c.get('content')]
        
        sentiments = [self._analyze_sentiment(content) for content in contents]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.5
        
        all_text = ' '.join(contents)
        keywords = self._extract_keywords(all_text, top_k=20)
        
        word_freq = Counter()
        for content in contents:
            words = jieba.cut(content)
            word_freq.update([w for w in words if w not in self.stopwords and len(w) > 1])
        
        return {
            'total_comments': len(comments),
            'avg_sentiment': avg_sentiment,
            'positive_ratio': sum(1 for s in sentiments if s > 0.6) / len(sentiments) if sentiments else 0,
            'negative_ratio': sum(1 for s in sentiments if s < 0.4) / len(sentiments) if sentiments else 0,
            'keywords': keywords,
            'word_freq': word_freq.most_common(50),
            'sentiments': sentiments
        }
    
    def analyze(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not comments:
            return {'error': '没有评论数据'}
        
        stats = self._calculate_stats(comments)
        
        analyzed_comments = []
        for i, comment in enumerate(comments):
            analyzed = comment.copy()
            analyzed['sentiment'] = stats['sentiments'][i] if i < len(stats['sentiments']) else 0.5
            analyzed['keywords'] = self._extract_keywords(comment.get('content', ''), top_k=5)
            analyzed_comments.append(analyzed)
        
        positive_comments = [c for c in analyzed_comments if c['sentiment'] > 0.6]
        negative_comments = [c for c in analyzed_comments if c['sentiment'] < 0.4]
        
        return {
            'stats': stats,
            'comments': analyzed_comments,
            'positive_comments': positive_comments,
            'negative_comments': negative_comments,
            'summary': self._generate_summary(stats)
        }
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        sentiment_desc = "积极" if stats['avg_sentiment'] > 0.6 else "消极" if stats['avg_sentiment'] < 0.4 else "中立"
        return f"共{stats['total_comments']}条评论，整体情感倾向{sentiment_desc}（{stats['avg_sentiment']:.2%}），正面评论占{stats['positive_ratio']:.1%}，负面评论占{stats['negative_ratio']:.1%}。"