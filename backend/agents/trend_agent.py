"""
Xトレンド記事生成エージェント
"""
from typing import Dict, Optional, List
import asyncio
from agents.theme_agent import ThemeAgent
from services.trend_scraper import TrendScraper

# グローバルなTrendScraperインスタンスを使用（バックグラウンド更新を共有）
_global_trend_scraper = None

def get_global_trend_scraper() -> TrendScraper:
    """グローバルなTrendScraperインスタンスを取得"""
    global _global_trend_scraper
    if _global_trend_scraper is None:
        _global_trend_scraper = TrendScraper()
    return _global_trend_scraper

class TrendAgent:
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.theme_agent = ThemeAgent(openai_api_key, gemini_api_key)
        # グローバルインスタンスを使用（バックグラウンド更新を共有）
        self.trend_scraper = get_global_trend_scraper()
    
    async def initialize(self):
        """初期化（互換性のため残す）"""
        pass
    
    async def get_trends(self, limit: int = 50, use_cache: bool = True) -> List[Dict[str, str]]:
        """
        Xのトレンドを取得（twittrend.jpから取得、日本語のトレンドを優先）
        
        Args:
            limit: 取得するトレンドの数（最大50）
            use_cache: キャッシュを使用するか（デフォルト: True）
        
        Returns:
            トレンドのリスト [{"keyword": "トレンド名", "tweet_count": 数値またはNone}]
        """
        try:
            # TrendScraperを使用してtwittrend.jpからトレンドを取得
            trends = await self.trend_scraper.get_trends(limit=limit, use_cache=use_cache)
            return trends
        except Exception as e:
            print(f"トレンド取得エラー: {str(e)}")
            # エラー時はフォールバックデータを返す
            return self._get_fallback_trends(limit)
    
    def _get_fallback_trends(self, limit: int) -> List[Dict[str, str]]:
        """フォールバック用の日本語トレンドデータ（20件）"""
        fallback_trends = [
            {"keyword": "AI", "tweet_count": None},
            {"keyword": "プログラミング", "tweet_count": None},
            {"keyword": "起業", "tweet_count": None},
            {"keyword": "投資", "tweet_count": None},
            {"keyword": "健康", "tweet_count": None},
            {"keyword": "テクノロジー", "tweet_count": None},
            {"keyword": "ビジネス", "tweet_count": None},
            {"keyword": "教育", "tweet_count": None},
            {"keyword": "ライフスタイル", "tweet_count": None},
            {"keyword": "エンターテイメント", "tweet_count": None},
            {"keyword": "副業", "tweet_count": None},
            {"keyword": "在宅ワーク", "tweet_count": None},
            {"keyword": "ママ", "tweet_count": None},
            {"keyword": "パパ", "tweet_count": None},
            {"keyword": "節約", "tweet_count": None},
            {"keyword": "ダイエット", "tweet_count": None},
            {"keyword": "旅行", "tweet_count": None},
            {"keyword": "グルメ", "tweet_count": None},
            {"keyword": "スポーツ", "tweet_count": None},
            {"keyword": "映画", "tweet_count": None},
        ]
        return fallback_trends[:limit]
    
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

