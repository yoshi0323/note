"""
SQLiteデータベース管理（セッション別データ分離）
"""
import sqlite3
import json
from typing import Dict, Optional, List
from datetime import datetime

DB_FILE = "user_data.db"

def init_db():
    """データベースを初期化"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 既存のテーブル構造を確認
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # テーブルが存在しない場合は作成
    if not columns:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                session_id TEXT PRIMARY KEY,
                settings TEXT,
                prompt_settings TEXT,
                articles TEXT,
                schedules TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        # schedulesカラムが存在しない場合は追加
        if 'schedules' not in columns:
            cursor.execute("ALTER TABLE user_data ADD COLUMN schedules TEXT")
    
    conn.commit()
    conn.close()

def get_default_data() -> Dict:
    """デフォルトデータを返す"""
    return {
        "settings": {
            "note_id": "",
            "note_password": "",
            "openai_api_key": "",
            "gemini_api_key": ""
        },
        "prompt_settings": {
            "tone": "明るい",
            "length": "2000-3000",
            "other_conditions": ""
        },
        "articles": [],
        "schedules": []
    }

def get_user_data(session_id: str) -> Dict:
    """ユーザーデータを取得（なければデフォルトを作成）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # カラム数を確認して適切なSELECT文を構築
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'schedules' in columns:
        cursor.execute("SELECT settings, prompt_settings, articles, schedules FROM user_data WHERE session_id = ?", (session_id,))
    else:
        cursor.execute("SELECT settings, prompt_settings, articles FROM user_data WHERE session_id = ?", (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        result = {
            "settings": json.loads(row[0]) if row[0] else get_default_data()["settings"],
            "prompt_settings": json.loads(row[1]) if row[1] else get_default_data()["prompt_settings"],
            "articles": json.loads(row[2]) if row[2] else []
        }
        if len(row) > 3 and row[3]:
            result["schedules"] = json.loads(row[3]) if row[3] else []
        else:
            result["schedules"] = []
        return result
    else:
        # 新規ユーザー - デフォルトデータを作成
        default_data = get_default_data()
        save_user_data(session_id, default_data)
        return default_data

def save_user_data(session_id: str, data: Dict):
    """ユーザーデータを保存"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # カラム数を確認
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'schedules' in columns:
        cursor.execute("""
            INSERT OR REPLACE INTO user_data (session_id, settings, prompt_settings, articles, schedules, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            session_id,
            json.dumps(data.get("settings", {}), ensure_ascii=False),
            json.dumps(data.get("prompt_settings", {}), ensure_ascii=False),
            json.dumps(data.get("articles", []), ensure_ascii=False),
            json.dumps(data.get("schedules", []), ensure_ascii=False)
        ))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO user_data (session_id, settings, prompt_settings, articles, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            session_id,
            json.dumps(data.get("settings", {}), ensure_ascii=False),
            json.dumps(data.get("prompt_settings", {}), ensure_ascii=False),
            json.dumps(data.get("articles", []), ensure_ascii=False)
        ))
    
    conn.commit()
    conn.close()

def update_user_settings(session_id: str, settings: Dict):
    """設定のみを更新"""
    print(f"[DB] update_user_settings called for session: {session_id[:8]}...")
    data = get_user_data(session_id)
    print(f"[DB] 現在のデータ: {data['settings']}")
    data["settings"] = settings
    print(f"[DB] 更新後のデータ: {data['settings']}")
    save_user_data(session_id, data)
    print(f"[DB] データベースに保存しました")

def update_user_prompt_settings(session_id: str, prompt_settings: Dict):
    """プロンプト設定のみを更新"""
    data = get_user_data(session_id)
    data["prompt_settings"] = prompt_settings
    save_user_data(session_id, data)

def add_user_article(session_id: str, article: Dict):
    """記事を追加"""
    data = get_user_data(session_id)
    data["articles"].append(article)
    save_user_data(session_id, data)

def get_user_articles(session_id: str) -> list:
    """ユーザーの記事一覧を取得"""
    data = get_user_data(session_id)
    return data["articles"]

def get_user_article(session_id: str, article_id: int) -> Optional[Dict]:
    """特定の記事を取得"""
    articles = get_user_articles(session_id)
    return next((a for a in articles if a.get("id") == article_id), None)

def update_user_article(session_id: str, article_id: int, updates: Dict):
    """記事を更新"""
    data = get_user_data(session_id)
    articles = data["articles"]
    for i, article in enumerate(articles):
        if article.get("id") == article_id:
            articles[i] = {**article, **updates}
            break
    data["articles"] = articles
    save_user_data(session_id, data)

def delete_user_article(session_id: str, article_id: int):
    """記事を削除"""
    data = get_user_data(session_id)
    data["articles"] = [a for a in data["articles"] if a.get("id") != article_id]
    save_user_data(session_id, data)

def get_user_schedules(session_id: str) -> List[Dict]:
    """ユーザーのスケジュール一覧を取得"""
    data = get_user_data(session_id)
    return data.get("schedules", [])

def add_user_schedule(session_id: str, schedule: Dict):
    """スケジュールを追加"""
    data = get_user_data(session_id)
    if "schedules" not in data:
        data["schedules"] = []
    data["schedules"].append(schedule)
    save_user_data(session_id, data)

def delete_user_schedule(session_id: str, schedule_id: str):
    """スケジュールを削除"""
    data = get_user_data(session_id)
    data["schedules"] = [s for s in data.get("schedules", []) if s.get("schedule_id") != schedule_id]
    save_user_data(session_id, data)

