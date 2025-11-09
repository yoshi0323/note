from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import sqlite3
import sys
import asyncio
import time
from dotenv import load_dotenv
from agents import ThemeAgent, TrendAgent, XPostAgent
from services.note_service import NoteService
from services.auto_post_service import AutoPostService
from database import init_db, get_user_data, save_user_data, update_user_settings, update_user_prompt_settings, add_user_article, get_user_articles, get_user_article, update_user_article, delete_user_article, get_user_schedules, add_user_schedule, delete_user_schedule

# Windows環境でのasyncio問題を修正
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

# データベース初期化
init_db()

app = FastAPI(title="Note下書き投稿システム")
auto_post_service = AutoPostService()

# セッション管理（セッションID: 有効フラグ）
active_sessions = {}

# CORS設定
# 環境変数から許可オリジンを取得（カンマ区切り）
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # 環境変数が設定されている場合はそれを使用
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # デフォルト: ローカル開発環境 + 本番環境（Firebase Hosting）
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://note-c801b.web.app",
        "https://note-c801b.firebaseapp.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッション管理関数
def create_session() -> str:
    """新しいセッションを作成"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = True
    return session_id

def validate_session(session_id: Optional[str]) -> str:
    """セッションIDを検証（データベースに存在すれば有効）"""
    if not session_id:
        raise HTTPException(status_code=401, detail="セッションIDが必要です。ログインしてください。")
    
    # アクティブセッションに存在するか確認
    if session_id in active_sessions:
        return session_id
    
    # データベースに存在するか確認（再起動後も有効）
    try:
        from database import DB_FILE
        # データベースにセッションIDが存在するか確認
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT session_id FROM user_data WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # データベースに存在すれば、セッションをアクティブに復元
            active_sessions[session_id] = True
            print(f"[セッション復元] セッションID {session_id[:8]}... をデータベースから復元しました")
            return session_id
        else:
            # データベースにも存在しない場合はエラー
            raise HTTPException(status_code=401, detail="セッションが無効です。再ログインしてください。")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[セッション検証エラー] {str(e)}")
        raise HTTPException(status_code=401, detail="セッションが無効です。再ログインしてください。")

# 認証モデル
class LoginRequest(BaseModel):
    password: str

# スケジュールモデル
class ScheduleRequest(BaseModel):
    schedule_type: str  # "daily" or "weekly"
    day_of_week: Optional[int] = None  # 0=月曜日, 6=日曜日
    time: str  # HH:MM形式
    article_id: Optional[int] = None  # 記事ID（既存記事の場合）
    theme: Optional[str] = None  # テーマ（新規生成の場合）
    trend_keyword: Optional[str] = None  # トレンドキーワード（新規生成の場合）
    llm_provider: str = "openai"  # LLMプロバイダー

class SettingsRequest(BaseModel):
    note_id: str
    note_password: str
    openai_api_key: str
    gemini_api_key: str

class PromptSettingsRequest(BaseModel):
    tone: str
    length: str
    other_conditions: str

class ArticleRequest(BaseModel):
    title: str
    content: str
    theme: Optional[str] = None

class AutoPostRequest(BaseModel):
    article_id: str
    scheduled_time: str

@app.get("/")
def read_root():
    return {"message": "Note下書き投稿システムAPI"}

@app.post("/api/auth/login")
def login(request: LoginRequest):
    """固定パスワードでログイン、セッションIDを発行"""
    if request.password == "note123":
        session_id = create_session()
        return {
            "success": True, 
            "message": "ログイン成功",
            "session_id": session_id
        }
    raise HTTPException(status_code=401, detail="パスワードが正しくありません")

@app.get("/api/settings")
def get_settings(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """設定を取得（セッション別）"""
    print(f"[GET /api/settings] セッションID: {x_session_id}")
    session_id = validate_session(x_session_id)
    print(f"[GET /api/settings] 検証済みセッションID: {session_id}")
    data = get_user_data(session_id)
    print(f"[GET /api/settings] 取得データ: {data['settings']}")
    return data["settings"]

@app.post("/api/settings")
def update_settings(request: SettingsRequest, x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """設定を更新（セッション別）"""
    print(f"[POST /api/settings] セッションID: {x_session_id}")
    print(f"[POST /api/settings] 受信データ: {request.dict()}")
    session_id = validate_session(x_session_id)
    print(f"[POST /api/settings] 検証済みセッションID: {session_id}")
    update_user_settings(session_id, request.dict())
    print(f"[POST /api/settings] 設定を保存しました")
    return {"success": True, "message": "設定を更新しました"}

@app.get("/api/prompt-settings")
def get_prompt_settings(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """プロンプト設定を取得（セッション別）"""
    session_id = validate_session(x_session_id)
    data = get_user_data(session_id)
    return data["prompt_settings"]

@app.post("/api/prompt-settings")
def update_prompt_settings(request: PromptSettingsRequest, x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """プロンプト設定を更新（セッション別）"""
    session_id = validate_session(x_session_id)
    update_user_prompt_settings(session_id, request.dict())
    return {"success": True, "message": "プロンプト設定を更新しました"}

@app.get("/api/themes")
def get_themes():
    themes = [
        "テクノロジー",
        "ビジネス",
        "ライフスタイル",
        "エンターテイメント",
        "教育",
        "健康・美容",
        "旅行",
        "料理",
        "スポーツ",
        "アート・デザイン",
        "音楽",
        "読書",
        "投資・金融",
        "子育て",
        "自己啓発",
        "プログラミング",
        "AI・機械学習",
        "起業",
        "マーケティング",
        "心理学"
    ]
    return {"themes": themes}

@app.post("/api/articles/generate/theme")
async def generate_theme_article(
    theme: str = Query(...), 
    llm_provider: str = Query("openai"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """テーマ別記事生成（セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        data = get_user_data(session_id)
        settings = data["settings"]
        prompt_settings = data["prompt_settings"]
        
        agent = ThemeAgent(
            openai_api_key=settings.get("openai_api_key") if llm_provider == "openai" else None,
            gemini_api_key=settings.get("gemini_api_key") if llm_provider == "gemini" else None
        )
        
        result = agent.generate_article(
            theme=theme,
            provider=llm_provider,
            tone=prompt_settings.get("tone", "明るい"),
            length=prompt_settings.get("length", "2000-3000"),
            other_conditions=prompt_settings.get("other_conditions", "")
        )
        
        # 記事を保存
        articles = get_user_articles(session_id)
        article = {
            "id": len(articles) + 1,
            "title": result["title"],
            "content": result["content"],
            "theme": theme
        }
        add_user_article(session_id, article)
        
        return {"success": True, "article": article}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/articles/generate/trend")
async def generate_trend_article(
    theme: str = Query(...), 
    trend_keyword: str = Query(...), 
    llm_provider: str = Query("openai"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Xトレンド記事生成（セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        data = get_user_data(session_id)
        settings = data["settings"]
        prompt_settings = data["prompt_settings"]
        
        agent = TrendAgent(
            openai_api_key=settings.get("openai_api_key") if llm_provider == "openai" else None,
            gemini_api_key=settings.get("gemini_api_key") if llm_provider == "gemini" else None
        )
        await agent.initialize()
        
        result = await agent.generate_article_from_trend(
            trend_keyword=trend_keyword,
            theme=theme,
            provider=llm_provider,
            tone=prompt_settings.get("tone", "明るい"),
            length=prompt_settings.get("length", "2000-3000"),
            other_conditions=prompt_settings.get("other_conditions", "")
        )
        
        # 記事を保存
        articles = get_user_articles(session_id)
        article = {
            "id": len(articles) + 1,
            "title": result["title"],
            "content": result["content"],
            "theme": theme,
            "trend_keyword": trend_keyword
        }
        add_user_article(session_id, article)
        
        return {"success": True, "article": article}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/articles/generate/manual")
async def generate_manual_article(
    request: ArticleRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """手動記事生成（編集可能・セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        articles = get_user_articles(session_id)
        article = {
            "id": len(articles) + 1,
            "title": request.title,
            "content": request.content,
            "theme": request.theme
        }
        add_user_article(session_id, article)
        return {"success": True, "article": article}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/articles")
def create_article(
    request: ArticleRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    session_id = validate_session(x_session_id)
    articles = get_user_articles(session_id)
    article = {
        "id": len(articles) + 1,
        **request.dict()
    }
    add_user_article(session_id, article)
    return {"success": True, "article": article}

@app.get("/api/articles")
def get_articles(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """記事一覧取得（セッション別）"""
    session_id = validate_session(x_session_id)
    articles = get_user_articles(session_id)
    return {"articles": articles}

@app.get("/api/articles/{article_id}")
def get_article(
    article_id: int,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """記事取得（セッション別）"""
    session_id = validate_session(x_session_id)
    article = get_user_article(session_id, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    return {"article": article}

@app.get("/api/trends")
async def get_trends(
    limit: int = 10,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Xトレンド取得（セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        data = get_user_data(session_id)
        settings = data["settings"]
        agent = TrendAgent(
            openai_api_key=settings.get("openai_api_key"),
            gemini_api_key=settings.get("gemini_api_key")
        )
        await agent.initialize()
        trends = await agent.get_trends(limit=limit)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/articles/{article_id}/post")
async def post_draft(
    article_id: int, 
    scheduled_time: Optional[str] = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """下書き投稿（自動投稿対応・ブラウザスクレイピング・セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        # 記事を取得
        article = get_user_article(session_id, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        
        data = get_user_data(session_id)
        settings = data["settings"]
        note_id = settings.get("note_id", "").strip()
        note_password = settings.get("note_password", "").strip()
        
        # 設定の確認
        if not note_id or not note_password:
            raise HTTPException(
                status_code=400, 
                detail="note.comのID/パスワードが設定されていません。設定画面で入力してください。"
            )
        
        note_service = NoteService(
            note_id=note_id,
            note_password=note_password
        )
        
        if scheduled_time:
            # 自動投稿をスケジュール
            async def post_callback(aid: int):
                art = get_user_article(session_id, aid)
                if art:
                    await note_service.post_draft(art["title"], art["content"])
            
            auto_post_service.schedule_post(
                article_id=article_id,
                scheduled_time=scheduled_time,
                post_callback=post_callback
            )
            return {"success": True, "message": f"投稿をスケジュールしました: {scheduled_time}"}
        else:
            # 即座に投稿（ブラウザスクレイピングで自動実行）
            result = await note_service.post_draft(article["title"], article["content"])
            # 投稿済みフラグを設定
            update_user_article(session_id, article_id, {"posted": True, "posted_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            return {
                "success": True, 
                "message": "下書きを保存しました",
                "result": result
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下書き投稿エラー: {str(e)}")

@app.delete("/api/articles/{article_id}")
def delete_article(
    article_id: int,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """記事を削除"""
    try:
        session_id = validate_session(x_session_id)
        article = get_user_article(session_id, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        
        delete_user_article(session_id, article_id)
        return {"success": True, "message": "記事を削除しました"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schedules")
def get_schedules(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """スケジュール一覧を取得"""
    try:
        session_id = validate_session(x_session_id)
        schedules = get_user_schedules(session_id)
        return {"success": True, "schedules": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedules")
async def add_schedule(
    request: ScheduleRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """スケジュールを追加"""
    try:
        session_id = validate_session(x_session_id)
        schedule_id = str(uuid.uuid4())
        
        # スケジュール情報を作成
        schedule_info = {
            "schedule_id": schedule_id,
            "schedule_type": request.schedule_type,
            "day_of_week": request.day_of_week,
            "time": request.time,
            "article_id": request.article_id,
            "theme": request.theme,
            "trend_keyword": request.trend_keyword,
            "llm_provider": request.llm_provider,
            "status": "active",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # データベースに保存
        add_user_schedule(session_id, schedule_info)
        
        # AutoPostServiceに登録
        data = get_user_data(session_id)
        settings = data["settings"]
        note_id = settings.get("note_id", "").strip()
        note_password = settings.get("note_password", "").strip()
        
        if not note_id or not note_password:
            raise HTTPException(
                status_code=400,
                detail="note.comのID/パスワードが設定されていません。設定画面で入力してください。"
            )
        
        async def generate_and_post_callback():
            """記事生成→投稿のコールバック"""
            try:
                # 記事を生成
                prompt_settings = data["prompt_settings"]
                if request.trend_keyword:
                    # トレンド記事生成
                    agent = TrendAgent(
                        openai_api_key=settings.get("openai_api_key") if request.llm_provider == "openai" else None,
                        gemini_api_key=settings.get("gemini_api_key") if request.llm_provider == "gemini" else None
                    )
                    await agent.initialize()
                    result = await agent.generate_article_from_trend(
                        trend_keyword=request.trend_keyword,
                        theme=request.theme,
                        provider=request.llm_provider,
                        tone=prompt_settings.get("tone", "明るい"),
                        length=prompt_settings.get("length", "2000-3000"),
                        other_conditions=prompt_settings.get("other_conditions", "")
                    )
                else:
                    # テーマ記事生成
                    agent = ThemeAgent(
                        openai_api_key=settings.get("openai_api_key") if request.llm_provider == "openai" else None,
                        gemini_api_key=settings.get("gemini_api_key") if request.llm_provider == "gemini" else None
                    )
                    result = agent.generate_article(
                        theme=request.theme,
                        provider=request.llm_provider,
                        tone=prompt_settings.get("tone", "明るい"),
                        length=prompt_settings.get("length", "2000-3000"),
                        other_conditions=prompt_settings.get("other_conditions", "")
                    )
                
                # 記事を保存
                articles = get_user_articles(session_id)
                article = {
                    "id": len(articles) + 1,
                    "title": result["title"],
                    "content": result["content"],
                    "theme": request.theme,
                    "trend_keyword": request.trend_keyword
                }
                add_user_article(session_id, article)
                
                # 投稿
                note_service = NoteService(note_id=note_id, note_password=note_password)
                await note_service.post_draft(article["title"], article["content"])
                update_user_article(session_id, article["id"], {"posted": True, "posted_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            except Exception as e:
                print(f"[スケジュール実行エラー] {str(e)}")
        
        # コールバック関数を決定
        if request.article_id:
            # 既存記事を投稿
            async def post_callback():
                note_service = NoteService(note_id=note_id, note_password=note_password)
                article = get_user_article(session_id, request.article_id)
                if article:
                    await note_service.post_draft(article["title"], article["content"])
                    update_user_article(session_id, request.article_id, {"posted": True, "posted_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            callback = post_callback
        else:
            # 新規生成→投稿
            callback = generate_and_post_callback
        
        # AutoPostServiceに登録
        auto_post_service.add_schedule(
            schedule_id=schedule_id,
            article_id=request.article_id or 0,
            schedule_type=request.schedule_type,
            day_of_week=request.day_of_week,
            time_str=request.time,
            post_callback=callback
        )
        
        return {"success": True, "message": "スケジュールを追加しました", "schedule": schedule_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """スケジュールを削除"""
    try:
        session_id = validate_session(x_session_id)
        schedules = get_user_schedules(session_id)
        schedule = next((s for s in schedules if s.get("schedule_id") == schedule_id), None)
        if not schedule:
            raise HTTPException(status_code=404, detail="スケジュールが見つかりません")
        
        # データベースから削除
        delete_user_schedule(session_id, schedule_id)
        
        # AutoPostServiceから削除
        auto_post_service.remove_schedule(schedule_id)
        
        return {"success": True, "message": "スケジュールを削除しました"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/articles/{article_id}/x-post")
async def generate_x_post(
    article_id: int, 
    llm_provider: str = Query("openai"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """X投稿用本文生成（セッション別）"""
    try:
        session_id = validate_session(x_session_id)
        # 記事を取得
        article = get_user_article(session_id, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="記事が見つかりません")
        
        data = get_user_data(session_id)
        settings = data["settings"]
        agent = XPostAgent(
            openai_api_key=settings.get("openai_api_key") if llm_provider == "openai" else None,
            gemini_api_key=settings.get("gemini_api_key") if llm_provider == "gemini" else None
        )
        
        result = agent.generate_x_post(
            article_title=article["title"],
            article_content=article["content"],
            provider=llm_provider
        )
        
        return {"success": True, "x_post": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

