"""
Xトレンド記事生成エージェント
"""
from typing import Dict, Optional, List
import asyncio
from twscrape import API, gather
from agents.theme_agent import ThemeAgent

class TrendAgent:
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.theme_agent = ThemeAgent(openai_api_key, gemini_api_key)
        self.api = None
    
    async def initialize(self):
        """twscrape APIを初期化"""
        try:
            self.api = API()
            await self.api.pool.login_all()
        except Exception as e:
            print(f"twscrape初期化エラー: {str(e)}")
            # エラーが発生しても続行（モックデータを使用）
    
    async def get_trends(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Xのトレンドを取得
        
        Args:
            limit: 取得するトレンドの数
        
        Returns:
            トレンドのリスト
        """
        try:
            if self.api:
                # 実際のAPI呼び出し（実装はtwscrapeの仕様に依存）
                # ここではモックデータを返す
                pass
        except Exception as e:
            print(f"トレンド取得エラー: {str(e)}")
        
        # モックデータ（実際の実装ではtwscrapeから取得）
        mock_trends = [
            {"keyword": "AI", "tweet_count": 50000},
            {"keyword": "プログラミング", "tweet_count": 30000},
            {"keyword": "起業", "tweet_count": 25000},
            {"keyword": "投資", "tweet_count": 40000},
            {"keyword": "健康", "tweet_count": 35000},
        ]
        return mock_trends[:limit]
    
    async def generate_article_from_trend(
        self,
        trend_keyword: str,
        theme: str,
        provider: str = "openai",
        tone: str = "明るい",
        length: str = "2000-3000",
        other_conditions: str = ""
    ) -> Dict[str, str]:
        """
        トレンドキーワードとテーマに基づいて記事を生成
        
        Args:
            trend_keyword: Xのトレンドキーワード
            theme: 記事のテーマ
            provider: LLMプロバイダー
            tone: 文章のトーン
            length: 文章の長さ
            other_conditions: その他の条件
        
        Returns:
            生成された記事のタイトルと本文
        """
        # トレンドキーワードを条件に追加
        enhanced_conditions = f"{other_conditions}\n\n現在Xで話題になっている「{trend_keyword}」についても触れてください。" if other_conditions else f"現在Xで話題になっている「{trend_keyword}」についても触れてください。"
        
        return self.theme_agent.generate_article(
            theme=theme,
            provider=provider,
            tone=tone,
            length=length,
            other_conditions=enhanced_conditions
        )

