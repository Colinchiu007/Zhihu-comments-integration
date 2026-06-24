"""数据存储模块 - 保存原文和评论到JSON文件"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DataStorage:
    """数据存储器"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_answer_dir(self, question_id: str, answer_id: str) -> Path:
        """获取回答数据目录"""
        answer_dir = self.data_dir / question_id / answer_id
        answer_dir.mkdir(parents=True, exist_ok=True)
        return answer_dir
    
    def save_answer(self, data: Dict[str, Any]) -> str:
        """
        保存回答数据
        
        Args:
            data: 包含原文和评论的数据
            
        Returns:
            保存的文件路径
        """
        question_id = data.get('question_id', 'unknown')
        answer_id = data.get('answer_id', 'unknown')
        
        answer_dir = self._get_answer_dir(question_id, answer_id)
        
        # 保存完整数据
        file_path = answer_dir / 'answer.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 单独保存原文
        if data.get('original'):
            original_path = answer_dir / 'original.json'
            with open(original_path, 'w', encoding='utf-8') as f:
                json.dump(data['original'], f, ensure_ascii=False, indent=2)
        
        # 单独保存评论
        if data.get('comments'):
            comments_path = answer_dir / 'comments.json'
            with open(comments_path, 'w', encoding='utf-8') as f:
                json.dump(data['comments'], f, ensure_ascii=False, indent=2)
        
        # 保存元信息
        metadata = {
            'answer_id': answer_id,
            'question_id': question_id,
            'url': data.get('url', ''),
            'original_saved': data.get('original') is not None,
            'comment_count': len(data.get('comments', [])),
            'scraped_at': data.get('scraped_at', datetime.now().isoformat()),
            'saved_at': datetime.now().isoformat()
        }
        metadata_path = answer_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def load_answer(self, question_id: str, answer_id: str) -> Optional[Dict[str, Any]]:
        """
        加载回答数据
        
        Args:
            question_id: 问题ID
            answer_id: 回答ID
            
        Returns:
            回答数据，如果不存在则返回None
        """
        answer_dir = self.data_dir / question_id / answer_id
        file_path = answer_dir / 'answer.json'
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def list_answers(self, question_id: Optional[str] = None) -> list:
        """
        列出已保存的回答
        
        Args:
            question_id: 可选，指定问题ID
            
        Returns:
            回答列表
        """
        answers = []
        
        if question_id:
            # 列出指定问题下的所有回答
            question_dir = self.data_dir / question_id
            if question_dir.exists():
                for answer_dir in question_dir.iterdir():
                    if answer_dir.is_dir():
                        metadata_path = answer_dir / 'metadata.json'
                        if metadata_path.exists():
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                answers.append(metadata)
                        else:
                            # 没有metadata.json，创建一个基本的
                            answers.append({
                                'answer_id': answer_dir.name,
                                'question_id': question_id
                            })
        else:
            # 列出所有问题下的所有回答
            for question_dir in self.data_dir.iterdir():
                if question_dir.is_dir():
                    for answer_dir in question_dir.iterdir():
                        if answer_dir.is_dir():
                            metadata_path = answer_dir / 'metadata.json'
                            if metadata_path.exists():
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    answers.append(metadata)
                            else:
                                answers.append({
                                    'answer_id': answer_dir.name,
                                    'question_id': question_dir.name
                                })
        
        return answers
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        total_questions = 0
        total_answers = 0
        total_comments = 0
        
        for question_dir in self.data_dir.iterdir():
            if question_dir.is_dir():
                total_questions += 1
                for answer_dir in question_dir.iterdir():
                    if answer_dir.is_dir():
                        total_answers += 1
                        metadata_path = answer_dir / 'metadata.json'
                        if metadata_path.exists():
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                total_comments += metadata.get('comment_count', 0)
                        else:
                            # 没有metadata.json，尝试从answer文件获取评论数
                            answer_path = answer_dir / 'answer.json'
                            if answer_path.exists():
                                with open(answer_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    total_comments += len(data.get('comments', []))
        
        return {
            'total_questions': total_questions,
            'total_answers': total_answers,
            'total_comments': total_comments,
            'data_dir': str(self.data_dir)
        }


if __name__ == '__main__':
    # 测试
    storage = DataStorage('test_data')
    
    test_data = {
        'question_id': '123456',
        'answer_id': '789012',
        'url': 'https://www.zhihu.com/question/123456/answer/789012',
        'original': {'content': '测试原文', 'author': '测试作者'},
        'comments': [
            {'author': '用户1', 'content': '评论1'},
            {'author': '用户2', 'content': '评论2'}
        ],
        'scraped_at': datetime.now().isoformat()
    }
    
    file_path = storage.save_answer(test_data)
    print(f'保存成功: {file_path}')
    
    # 加载
    loaded = storage.load_answer('123456', '789012')
    print(f'加载成功: {loaded is not None}')
    
    # 统计
    stats = storage.get_statistics()
    print(f'统计: {stats}')
