"""
X投稿用本文生成エージェント
"""
from typing import Dict, Optional
import openai
import google.generativeai as genai

class XPostAgent:
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        
        if openai_api_key:
            openai.api_key = openai_api_key
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
    
    def generate_x_post(
        self,
        article_title: str,
        article_content: str,
        provider: str = "openai"
    ) -> Dict[str, str]:
        """
        記事からX投稿用の本文を生成
        
        Args:
            article_title: 記事のタイトル
            article_content: 記事の本文
            provider: LLMプロバイダー
        
        Returns:
            X投稿用の本文とハッシュタグ
        """
        prompt = f"""以下の記事を要約して、X（旧Twitter）向けの投稿文を作成してください。

タイトル: {article_title}
本文: {article_content[:1000]}...

要件:
- 280文字以内
- 記事への興味を引く内容
- 適切なハッシュタグを3-5個追加
- 記事のリンクを想定した「続きはnoteで」などの誘導文を含める
- 絵文字を適度に使用して親しみやすくする
- Markdown記号は使用しない

出力形式:
投稿文: [本文]
ハッシュタグ: [ハッシュタグ1] [ハッシュタグ2] ...
"""
        
        if provider == "openai" and self.openai_api_key:
            return self._generate_with_openai(prompt)
        elif provider == "gemini" and self.gemini_api_key:
            return self._generate_with_gemini(prompt)
        else:
            raise ValueError(f"プロバイダー {provider} が利用できません")
    
    def _generate_with_openai(self, prompt: str) -> Dict[str, str]:
        """OpenAI APIを使用"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはSNSマーケティングの専門家です。Markdown記号は使用せず、絵文字を適度に使用して親しみやすい投稿文を作成してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
        except Exception as e:
            raise Exception(f"OpenAI API エラー: {str(e)}")
    
    def _generate_with_gemini(self, prompt: str) -> Dict[str, str]:
        """Gemini APIを使用"""
        try:
            # Gemini 2.5 Flash - 無料APIで最高機能のモデル
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            content = response.text
            return self._parse_response(content)
        except Exception as e:
            raise Exception(f"Gemini API エラー: {str(e)}")
    
    def _parse_response(self, content: str) -> Dict[str, str]:
        """応答をパース"""
        lines = content.strip().split('\n')
        post_text = ""
        hashtags = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("投稿文:") or line.startswith("投稿文："):
                post_text = line.split(":", 1)[-1].split("：", 1)[-1].strip()
            elif line.startswith("ハッシュタグ:") or line.startswith("ハッシュタグ："):
                hashtag_text = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                # ハッシュタグを抽出
                import re
                hashtags = re.findall(r'#\w+', hashtag_text)
        
        # パースに失敗した場合は全体を投稿文として使用
        if not post_text:
            post_text = content.strip()
        
        # ハッシュタグを投稿文に追加
        if hashtags:
            hashtag_str = " ".join(hashtags)
            full_post = f"{post_text}\n\n{hashtag_str}"
        else:
            full_post = post_text
        
        return {
            "post_text": post_text,
            "hashtags": hashtags,
            "full_post": full_post
        }

