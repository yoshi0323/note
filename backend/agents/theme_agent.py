"""
テーマ別記事生成エージェント
"""
from typing import Dict, Optional
import openai
import google.generativeai as genai

class ThemeAgent:
    def __init__(self, openai_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        
        if openai_api_key:
            openai.api_key = openai_api_key
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
    
    def generate_article(
        self, 
        theme: str, 
        provider: str = "openai",
        tone: str = "明るい",
        length: str = "2000-3000",
        other_conditions: str = ""
    ) -> Dict[str, str]:
        """
        テーマに基づいて記事を生成
        
        Args:
            theme: テーマ名
            provider: LLMプロバイダー ("openai" or "gemini")
            tone: 文章のトーン
            length: 文章の長さ
            other_conditions: その他の条件
        
        Returns:
            生成された記事のタイトルと本文
        """
        prompt = self._build_prompt(theme, tone, length, other_conditions)
        
        if provider == "openai" and self.openai_api_key:
            return self._generate_with_openai(prompt)
        elif provider == "gemini" and self.gemini_api_key:
            return self._generate_with_gemini(prompt)
        else:
            raise ValueError(f"プロバイダー {provider} が利用できません")
    
    def generate_article_from_custom_prompt(
        self,
        custom_prompt: str,
        provider: str = "openai"
    ) -> Dict[str, str]:
        """
        カスタムプロンプトから記事を生成
        
        Args:
            custom_prompt: ユーザーが入力したカスタムプロンプト
            provider: LLMプロバイダー ("openai" or "gemini")
        
        Returns:
            生成された記事のタイトルと本文
        """
        # カスタムプロンプトにnote向けの基本指示を追加
        enhanced_prompt = f"""以下のプロンプトに基づいてnote向けの記事を作成してください。

{custom_prompt}

重要な注意事項：
- Markdown記号（#、##、###、**など）は一切使用しないでください
- 見出しも通常の文章として自然に書いてください
- 絵文字を適切に使用して、読みやすく親しみやすい文章にしてください
- タイトルには絵文字を含めないでください
- 本文には適度に絵文字を使用してください（段落の区切りや強調など）

記事は以下の形式で出力してください：
1. タイトル（1行、Markdown記号なし、絵文字なし）
2. 本文（読みやすく構成された記事、Markdown記号なし、適度に絵文字を使用）

タイトルと本文を明確に分けて出力してください。"""
        
        if provider == "openai" and self.openai_api_key:
            return self._generate_with_openai(enhanced_prompt)
        elif provider == "gemini" and self.gemini_api_key:
            return self._generate_with_gemini(enhanced_prompt)
        else:
            raise ValueError(f"プロバイダー {provider} が利用できません")
    
    def _build_prompt(self, theme: str, tone: str, length: str, other_conditions: str) -> str:
        """プロンプトを構築"""
        tone_map = {
            "明るい": "明るく前向きな",
            "丁寧": "丁寧で敬語を使った",
            "フランク": "フランクで親しみやすい"
        }
        tone_desc = tone_map.get(tone, tone)
        
        length_map = {
            "2000-3000": "2000文字から3000文字程度",
            "1000-2000": "1000文字から2000文字程度",
            "3000-5000": "3000文字から5000文字程度"
        }
        length_desc = length_map.get(length, length)
        
        prompt = f"""以下の条件でnote向けの記事を作成してください。

テーマ: {theme}
文章のトーン: {tone_desc}
文字数: {length_desc}
{other_conditions if other_conditions else ""}

重要な注意事項：
- Markdown記号（#、##、###、**など）は一切使用しないでください
- 見出しも通常の文章として自然に書いてください
- 絵文字を適切に使用して、読みやすく親しみやすい文章にしてください
- タイトルには絵文字を含めないでください
- 本文には適度に絵文字を使用してください（段落の区切りや強調など）

記事は以下の形式で出力してください：
1. タイトル（1行、Markdown記号なし、絵文字なし）
2. 本文（指定された文字数で、読みやすく構成された記事、Markdown記号なし、適度に絵文字を使用）

タイトルと本文を明確に分けて出力してください。"""
        return prompt
    
    def _generate_with_openai(self, prompt: str) -> Dict[str, str]:
        """OpenAI APIを使用して記事を生成"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはnote向けの記事を書くプロのライターです。Markdown記号は一切使用せず、自然な文章で書いてください。適度に絵文字を使用して親しみやすい文章にしてください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
        except Exception as e:
            raise Exception(f"OpenAI API エラー: {str(e)}")
    
    def _generate_with_gemini(self, prompt: str) -> Dict[str, str]:
        """Gemini APIを使用して記事を生成"""
        try:
            # Gemini 2.5 Flash - 無料APIで最高機能のモデル
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            content = response.text
            return self._parse_response(content)
        except Exception as e:
            raise Exception(f"Gemini API エラー: {str(e)}")
    
    def _parse_response(self, content: str) -> Dict[str, str]:
        """LLMの応答をパースしてタイトルと本文に分割"""
        import re
        
        # Markdown記号を削除
        def clean_markdown(text):
            # 見出し記号を削除
            text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
            # 太字記号を削除
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            # リスト記号を削除
            text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
            return text.strip()
        
        lines = content.strip().split('\n')
        title = ""
        body_lines = []
        found_title = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if found_title:
                    body_lines.append("")
                continue
            
            # タイトルを探す（最初の非空行、または「タイトル:」などのマーカーがある行）
            if not found_title:
                if line.startswith("タイトル:") or line.startswith("タイトル："):
                    title = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                    title = clean_markdown(title)
                    found_title = True
                elif not title and len(line) < 100:  # 短い行はタイトルの可能性が高い
                    title = clean_markdown(line)
                    found_title = True
                else:
                    body_lines.append(clean_markdown(line))
            else:
                body_lines.append(clean_markdown(line))
        
        # タイトルが見つからない場合は最初の行を使用
        if not title and lines:
            title = clean_markdown(lines[0].strip())
            body_lines = [clean_markdown(line.strip()) for line in lines[1:] if line.strip()]
        
        # 本文を結合（空行を適切に処理）
        body = '\n'.join(body_lines) if body_lines else clean_markdown(content)
        
        # 余分な空行を削除
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        return {
            "title": title or "無題",
            "content": body
        }

