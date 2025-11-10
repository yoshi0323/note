"""
X（Twitter）のトレンドをtwscrape/Playwrightで取得するサービス
バックグラウンドで定期的にトレンドを取得してキャッシュ
"""
from typing import List, Dict, Optional, Any
import asyncio
import threading
import schedule
import time
from datetime import datetime
import sys
from twscrape import API, AccountsPool
from playwright.async_api import async_playwright, TimeoutError as AsyncTimeoutError
from playwright.sync_api import sync_playwright, TimeoutError as SyncTimeoutError
from concurrent.futures import ThreadPoolExecutor

class TrendScraper:
    """Xのトレンドを取得するクラス（twscrape/Playwright使用、バックグラウンド更新対応）"""
    
    def __init__(self):
        self.api: Optional[API] = None
        self.pool: Optional[AccountsPool] = None
        self.initialized = False
        
        # キャッシュ機能
        self.cached_trends: List[Dict[str, str]] = []
        self.last_update: Optional[datetime] = None
        self.cache_valid_minutes: int = 30  # キャッシュの有効期限（分）
        
        # バックグラウンド更新
        self.is_background_running = False
        self.background_thread: Optional[threading.Thread] = None
        self.update_interval_minutes: int = 30  # 更新間隔（分）
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    def _check_login_state_sync(self, page) -> bool:
        """同期モードでログイン状態を確認"""
        try:
            current_url = page.url or ""
            if "login" in current_url.lower():
                return False
            nav_exists = (
                page.query_selector('nav[aria-label="メインナビゲーション"]')
                or page.query_selector('a[href="/home"]')
                or page.query_selector('a[href="/explore"]')
            )
            return bool(nav_exists)
        except Exception:
            return False

    async def _check_login_state_async(self, page) -> bool:
        """非同期モードでログイン状態を確認"""
        try:
            current_url = page.url or ""
            if "login" in current_url.lower():
                return False
            nav_exists = (
                await page.query_selector('nav[aria-label="メインナビゲーション"]')
                or await page.query_selector('a[href="/home"]')
                or await page.query_selector('a[href="/explore"]')
            )
            return bool(nav_exists)
        except Exception:
            return False

    def _extract_trend_keywords(self, texts: List[str], limit: int) -> List[Dict[str, str]]:
        """テキスト一覧からトレンドキーワードを抽出"""
        skip_phrases = [
            "Don't miss", "People on X", "Log in", "Sign up",
            "See new posts", "Something went wrong", "Retry",
            "New to X", "Create account", "Sign up with",
            "トレンド", "Trending", "今話題", "話題",
            "いま", "起きている", "見つけよう", "いち早く",
            "チェック", "ログイン", "アカウント作成", "新しいポスト",
            "問題が発生", "再読み込み", "やりなおす", "使ってみよう",
            "今すぐ登録", "タイムライン", "カスタマイズ", "Apple",
            "利用規約", "プライバシー", "Cookie", "アクセシビリティ",
            "広告情報", "もっと見る", "Try again", "fret",
            "Xを使ってみよう", "今すぐ登録して、タイムラインをカスタマイズしましょう。",
            "Appleのアカウントで登録", "利用規約", "プライバシー ポリシー",
            "Cookieの使用", "問題が発生しました。 再読み込みしてください。"
        ]
        skip_exact = {"|", "–", "-", "•", "• • •", "…", "© 2025 X Corp.", "© 2024 X Corp.", "© 2023 X Corp."}

        trends: List[Dict[str, str]] = []
        seen = set()

        for text in texts:
            if not text:
                continue
            normalized = text.strip()
            if not normalized or normalized in seen:
                continue
            if normalized in skip_exact:
                continue
            if any(phrase.lower() in normalized.lower() for phrase in skip_phrases):
                continue
            if len(normalized) > 100:
                continue

            keyword = normalized.replace('#', '').strip()
            if not keyword or keyword in seen:
                continue
            if keyword.startswith("http"):
                continue
            if "@" in keyword and " " not in keyword:
                continue
            if keyword.count('.') >= 2 and " " not in keyword:
                continue

            has_japanese = any('\u3040' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FFF' for char in keyword)
            is_short_en = all(char.isalnum() or char in (' ', '-', '_') for char in keyword) and len(keyword) < 25

            if has_japanese or is_short_en:
                trends.append({"keyword": keyword, "tweet_count": None})
                seen.add(keyword)
                print(f"[トレンドスクレイピング] トレンドを発見: {keyword}")
                if len(trends) >= limit:
                    break

        return trends

    def _perform_login_sync(self, page, username: str, password: str) -> bool:
        """同期モードでXにログイン"""
        login_url = "https://x.com/i/flow/login"
        username_selectors = [
            'input[name="text"]',
            'input[autocomplete="username"]',
            'input[type="text"]',
            'input[data-testid="ocfEnterTextTextInput"]',
        ]
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[autocomplete="current-password"]',
            'input[data-testid="ocfEnterTextTextInput"]',
        ]
        next_button_selectors = [
            'button:has-text("次へ")',
            'button[type="submit"]',
            'button[data-testid="ocfEnterTextNextButton"]',
            'div[role="button"]:has-text("次へ")',
            'div[data-testid="ocfEnterTextNextButton"]',
            'div[role="button"][data-testid="ocfEnterTextNextButton"]',
            'text="次へ"',
            'text="Next"',
            'button[role="button"]',
            'div[role="button"]',
        ]
        login_button_selectors = [
            'button:has-text("ログイン")',
            'button[data-testid="LoginForm_Login_Button"]',
            'button[data-testid="ocfEnterTextNextButton"]',
            'button[type="submit"]',
            'div[role="button"]:has-text("ログイン")',
        ]
        iframe_selectors = [
            'iframe[src*="identity"]',
            'iframe[src*="login"]',
            'iframe[src*="challenge"]',
        ]

        username = (username or "").strip()
        if username.startswith("@"):
            username = username[1:]

        try:
            page.goto(login_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(1500)
            page.wait_for_load_state("networkidle")
            page.keyboard.press("Escape")

            login_open_selectors = [
                'button[data-testid="loginButton"]',
                'a[href="/login"]',
                'div[role="button"]:has-text("ログイン")',
                'div[role="button"]:has-text("ログインする")',
            ]

            def open_login_modal():
                page.keyboard.press("Escape")
                for selector in login_open_selectors:
                    try:
                        btn = page.query_selector(selector)
                        if btn and btn.is_visible():
                            btn.click()
                            print(f"[トレンドスクレイピング] ログインモーダル用のボタンをクリック: {selector}")
                            page.wait_for_timeout(1500)
                            return True
                    except Exception:
                        continue
                return False

            def get_login_context():
                for _ in range(6):
                    for selector in iframe_selectors:
                        try:
                            iframe_el = page.query_selector(selector)
                            if iframe_el:
                                frame = iframe_el.content_frame()
                                if frame:
                                    print(f"[トレンドスクレイピング] ログイン用iframeを検出: {selector}")
                                    return frame
                        except Exception:
                            continue
                    page.wait_for_timeout(500)
                return page

            def context_candidates(login_context):
                if login_context:
                    yield login_context
                if login_context is not page:
                    yield page

            open_login_modal()
            login_context = get_login_context()

            username_input = None
            for attempt in range(3):
                for selector in username_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            element = ctx.wait_for_selector(selector, state="visible", timeout=5000)
                            if element:
                                element.fill(username)
                                print(f"[トレンドスクレイピング] ユーザー名を入力しました: {username[:3]}***")
                                username_input = element
                                break
                        except SyncTimeoutError:
                            continue
                        except Exception:
                            continue
                    if username_input:
                        break
                if username_input:
                    break
                open_login_modal()
                login_context = get_login_context()

            if not username_input:
                print("[警告] ユーザー名入力欄が見つかりませんでした")
                try:
                    page.screenshot(path="x_login_no_username.png", full_page=True)
                    print("[デバッグ] ユーザー名欄が見つからなかった時点のスクリーンショットを保存: x_login_no_username.png")
                except Exception as e:
                    print(f"[警告] スクリーンショット保存に失敗: {str(e)}")
                return False

            def find_next_button(handle) -> Optional[Any]:
                try:
                    text = handle.inner_text().strip()
                    if any(keyword in text for keyword in ["次へ", "Next", "次に"]):
                        return handle
                except Exception:
                    pass
                return None

            def click_next_button() -> bool:
                clicked = False
                
                # まず Enter キーでの送信を試す
                if username_input:
                    try:
                        username_input.press("Enter")
                        page.wait_for_timeout(800)
                        print("[トレンドスクレイピング] ユーザー名入力欄で Enter キー送信を試みました")
                        clicked = True
                    except Exception as e:
                        print(f"[警告] Enter キー送信に失敗: {str(e)}")
                
                for selector in next_button_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            candidate = ctx.query_selector(selector)

                            # ボタン候補が見つかったら、テキストを確認
                            btn = None
                            if candidate:
                                btn = find_next_button(candidate)

                            # セレクタが一般的なボタンを返した場合は、子要素を探索
                            if not btn and candidate and selector in ['button[role="button"]', 'div[role="button"]']:
                                child_buttons = candidate.query_selector_all('*')
                                for child in child_buttons:
                                    btn = find_next_button(child)
                                    if btn:
                                        break

                            # なお、該当しない場合は子要素全体を対象に探索
                            if not btn and candidate:
                                descendants = candidate.query_selector_all('*')
                                for child in descendants:
                                    btn = find_next_button(child)
                                    if btn:
                                        break

                            if not btn:
                                continue

                            if btn and btn.is_enabled():
                                # ボタンをクリックする前に、現在のURLとページ状態を記録
                                current_url = page.url
                                # Enterキーで送信を試みる（より確実）
                                try:
                                    btn.focus()
                                    page.wait_for_timeout(300)
                                    btn.click()
                                    print("[トレンドスクレイピング] 次へボタンをクリックしました")
                                    clicked = True
                                except Exception as e:
                                    print(f"[警告] クリックに失敗、Enterキーを試行: {str(e)}")
                                    # Enterキーで送信を試みる
                                    btn.press('Enter')
                                    print("[トレンドスクレイピング] Enterキーで送信しました")
                                    clicked = True
                                
                                # ページ遷移を待つ（最大10秒）
                                page.wait_for_timeout(1500)  # 最初の1.5秒待機
                                
                                # URLが変わったか、パスワード入力欄が表示されるまで待つ
                                for wait_count in range(10):
                                    page.wait_for_timeout(500)
                                    new_url = page.url
                                    
                                    # URLが変わった場合
                                    if new_url != current_url:
                                        print(f"[トレンドスクレイピング] ページ遷移を確認: {new_url}")
                                        return True
                                    
                                    # パスワード入力欄を確認
                                    for pwd_selector in password_selectors:
                                        try:
                                            pwd_input = ctx.query_selector(pwd_selector)
                                            if pwd_input and pwd_input.is_visible():
                                                print("[トレンドスクレイピング] パスワード入力欄の表示を確認")
                                                return True
                                        except:
                                            continue
                                    
                                    # ログインページに戻っている場合は失敗
                                    if "login" in new_url.lower() and wait_count > 3:
                                        print("[警告] ログインページに戻りました（追加ステップを確認）」")
                                        break
                                
                                # タイムアウトしても続行（ページが動いていない可能性）
                                print("[トレンドスクレイピング] ページ遷移の確認ができませんでしたが、続行します")
                                return True
                        except Exception as e:
                            print(f"[警告] 次へボタンクリック処理中にエラー: {str(e)}")
                            continue
                
                # ページ全体で Enter キーを試す（最終手段）
                if not clicked:
                    try:
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(800)
                        print("[トレンドスクレイピング] ページ全体で Enter キー送信を試みました")
                        clicked = True
                    except Exception as e:
                        print(f"[警告] ページ全体での Enter キー送信に失敗: {str(e)}")
                
                if clicked:
                    print("[トレンドスクレイピング] 次へボタンを押下しました（ページ状態確認は引き続き実施）")
                    return True
                print("[警告] 次へボタンが見つかりませんでした")
                return False

            if not click_next_button():
                return False

            login_context = get_login_context()

            password_input = None
            # パスワード入力欄が表示されるまで待つ（最大15秒）
            for attempt in range(15):
                for selector in password_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            password_input = ctx.query_selector(selector)
                            if password_input and password_input.is_visible():
                                print(f"[トレンドスクレイピング] パスワード入力欄を発見（試行{attempt+1}回目）")
                                break
                        except Exception:
                            continue
                    if password_input:
                        break

                if password_input:
                    break

                # 追加の確認（メール/電話番号の再入力など）に対応
                extra_input = None
                for selector in username_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            extra_input = ctx.query_selector(selector)
                            if extra_input and extra_input.is_visible():
                                extra_input.fill(username)
                                print("[トレンドスクレイピング] 追加の確認ステップにユーザー名を入力しました")
                                click_next_button()
                                page.wait_for_timeout(2000)
                                login_context = get_login_context()
                                break
                        except Exception:
                            continue
                    if extra_input:
                        break

                page.wait_for_timeout(1000)  # 1秒待機して再試行
                login_context = get_login_context()

            if not password_input:
                print("[警告] パスワード入力欄が見つかりませんでした")
                try:
                    page.screenshot(path="x_login_no_password.png", full_page=True)
                    print("[デバッグ] パスワード欄が見つからなかった時点のスクリーンショットを保存: x_login_no_password.png")
                except Exception as e:
                    print(f"[警告] スクリーンショット保存に失敗: {str(e)}")
                return False

            password_input.fill(password)
            print("[トレンドスクレイピング] パスワードを入力しました")
            page.wait_for_timeout(1000)

            login_button = None
            for selector in login_button_selectors:
                for ctx in context_candidates(login_context):
                    try:
                        login_button = ctx.query_selector(selector)
                        if login_button:
                            break
                    except Exception:
                        continue
                if login_button:
                    break

            if not login_button:
                print("[警告] ログインボタンが見つかりませんでした")
                try:
                    page.screenshot(path="x_login_no_button.png", full_page=True)
                    print("[デバッグ] ログインボタンが見つからなかった時点のスクリーンショットを保存: x_login_no_button.png")
                except Exception as e:
                    print(f"[警告] スクリーンショット保存に失敗: {str(e)}")
                return False

            # ログインボタンをクリックする前に、現在のURLを記録
            current_url = page.url
            login_button.click()
            print("[トレンドスクレイピング] ログインボタンをクリックしました")
            page.wait_for_timeout(2000)  # クリック後の初期待機

            # ログイン成功を確認（URL変更またはナビゲーション要素の出現を待つ）
            for i in range(30):  # 最大30秒待機
                page.wait_for_timeout(1000)
                new_url = page.url
                
                # URLが変わった場合（ログイン成功の可能性が高い）
                if new_url != current_url and "login" not in new_url.lower():
                    print(f"[トレンドスクレイピング] URL変更を確認: {new_url}")
                    if self._check_login_state_sync(page):
                        print("[トレンドスクレイピング] ログイン成功を確認しました（URL変更）")
                        return True
                
                # ナビゲーション要素で確認
                if self._check_login_state_sync(page):
                    print("[トレンドスクレイピング] ログイン成功を確認しました（ナビゲーション確認）")
                    return True
                
                # ログインページに戻っている場合は失敗
                if "login" in new_url.lower() and i > 5:
                    print("[警告] ログインページに戻りました。ログインに失敗した可能性があります。")
                    # スクリーンショットを保存（デバッグ用）
                    try:
                        page.screenshot(path='x_login_error.png')
                        print("[トレンドスクレイピング] エラー時のスクリーンショットを保存: x_login_error.png")
                    except:
                        pass
                    break
            
            print("[警告] ログイン成功の確認ができませんでした")
            return False

        except SyncTimeoutError:
            print("[警告] ログイン操作がタイムアウトしました")
            return False
        except Exception as e:
            print(f"[警告] Xログインエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    async def _perform_login_async(self, page, username: str, password: str) -> bool:
        """非同期モードでXにログイン"""
        login_url = "https://x.com/i/flow/login"
        username_selectors = [
            'input[name="text"]',
            'input[autocomplete="username"]',
            'input[type="text"]',
            'input[data-testid="ocfEnterTextTextInput"]',
        ]
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[autocomplete="current-password"]',
            'input[data-testid="ocfEnterTextTextInput"]',
        ]
        next_button_selectors = [
            'button:has-text("次へ")',
            'button[type="submit"]',
            'button[data-testid="ocfEnterTextNextButton"]',
            'div[role="button"]:has-text("次へ")',
        ]
        login_button_selectors = [
            'button:has-text("ログイン")',
            'button[data-testid="LoginForm_Login_Button"]',
            'button[data-testid="ocfEnterTextNextButton"]',
            'button[type="submit"]',
            'div[role="button"]:has-text("ログイン")',
        ]
        iframe_selectors = [
            'iframe[src*="identity"]',
            'iframe[src*="login"]',
            'iframe[src*="challenge"]',
        ]

        username = (username or "").strip()
        if username.startswith("@"):
            username = username[1:]

        try:
            await page.goto(login_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(1500)
            await page.wait_for_load_state("networkidle")
            await page.keyboard.press("Escape")

            login_open_selectors = [
                'button[data-testid="loginButton"]',
                'a[href="/login"]',
                'div[role="button"]:has-text("ログイン")',
                'div[role="button"]:has-text("ログインする")',
            ]

            async def open_login_modal():
                await page.keyboard.press("Escape")
                for selector in login_open_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn and await btn.is_visible():
                            await btn.click()
                            print(f"[トレンドスクレイピング] ログインモーダル用のボタンをクリック: {selector}")
                            await page.wait_for_timeout(1500)
                            return True
                    except Exception:
                        continue
                return False

            async def get_login_context():
                for _ in range(6):
                    for selector in iframe_selectors:
                        try:
                            iframe_el = await page.query_selector(selector)
                            if iframe_el:
                                frame = await iframe_el.content_frame()
                                if frame:
                                    print(f"[トレンドスクレイピング] ログイン用iframeを検出: {selector}")
                                    return frame
                        except Exception:
                            continue
                    await page.wait_for_timeout(500)
                return page

            def context_candidates(login_context):
                if login_context:
                    yield login_context
                if login_context is not page:
                    yield page

            await open_login_modal()
            login_context = await get_login_context()

            username_input = None
            for attempt in range(3):
                for selector in username_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            element = await ctx.wait_for_selector(selector, state="visible", timeout=5000)
                            if element:
                                await element.fill(username)
                                print(f"[トレンドスクレイピング] ユーザー名を入力しました: {username[:3]}***")
                                username_input = element
                                break
                        except AsyncTimeoutError:
                            continue
                        except Exception:
                            continue
                    if username_input:
                        break
                if username_input:
                    break
                await open_login_modal()
                login_context = await get_login_context()

            if not username_input:
                print("[警告] ユーザー名入力欄が見つかりませんでした")
                return False

            async def click_next_button() -> bool:
                for selector in next_button_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            btn = await ctx.query_selector(selector)
                            if btn:
                                await btn.click()
                                print("[トレンドスクレイピング] 次へボタンをクリックしました")
                                await page.wait_for_timeout(2000)
                                return True
                        except Exception:
                            continue
                print("[警告] 次へボタンが見つかりませんでした")
                return False

            if not await click_next_button():
                return False

            login_context = await get_login_context()

            password_input = None
            for attempt in range(3):
                for selector in password_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            password_input = await ctx.query_selector(selector)
                            if password_input and await password_input.is_visible():
                                break
                        except Exception:
                            continue
                    if password_input:
                        break

                if password_input:
                    break

                extra_input = None
                for selector in username_selectors:
                    for ctx in context_candidates(login_context):
                        try:
                            extra_input = await ctx.query_selector(selector)
                            if extra_input and await extra_input.is_visible():
                                await extra_input.fill(username)
                                print("[トレンドスクレイピング] 追加の確認ステップにユーザー名を入力しました")
                                await click_next_button()
                                break
                        except Exception:
                            continue
                    if extra_input:
                        break

                await page.wait_for_timeout(1500)
                login_context = await get_login_context()

            if not password_input:
                print("[警告] パスワード入力欄が見つかりませんでした")
                return False

            await password_input.fill(password)
            print("[トレンドスクレイピング] パスワードを入力しました")
            await page.wait_for_timeout(1000)

            login_button = None
            for selector in login_button_selectors:
                for ctx in context_candidates(login_context):
                    try:
                        login_button = await ctx.query_selector(selector)
                        if login_button:
                            break
                    except Exception:
                        continue
                if login_button:
                    break

            if not login_button:
                print("[警告] ログインボタンが見つかりませんでした")
                return False

            await login_button.click()
            print("[トレンドスクレイピング] ログインボタンをクリックしました")

            for _ in range(25):
                await page.wait_for_timeout(800)
                if await self._check_login_state_async(page):
                    print("[トレンドスクレイピング] ログイン成功を確認しました")
                    return True
            print("[警告] ログイン成功の確認ができませんでした")
            return False

        except AsyncTimeoutError:
            print("[警告] ログイン操作がタイムアウトしました")
            return False
        except Exception as e:
            print(f"[警告] Xログインエラー: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    async def initialize(self):
        """twscrape APIを初期化"""
        if self.initialized and self.api:
            return
        
        try:
            # AccountsPoolを作成
            self.pool = AccountsPool()
            # APIを初期化（poolが必要）
            self.api = API(self.pool)
            # アカウントでログイン
            await self.pool.login_all()
            self.initialized = True
            print("[情報] twscrape API初期化完了")
        except Exception as e:
            print(f"[警告] twscrape初期化エラー: {str(e)}")
            print("[情報] フォールバックデータを使用します")
            self.initialized = False
            self.api = None
            self.pool = None
    
    async def get_trends(self, limit: int = 50, use_cache: bool = True, x_username: Optional[str] = None, x_password: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Xのトレンドを取得（twittrend.jpから取得、キャッシュがあれば使用）
        
        Args:
            limit: 取得するトレンドの数（最大50）
            use_cache: キャッシュを使用するか（デフォルト: True）
            x_username: 互換性のため残す（使用しない）
            x_password: 互換性のため残す（使用しない）
        
        Returns:
            トレンドのリスト [{"keyword": "トレンド名", "tweet_count": 数値}]
        """
        # キャッシュが有効な場合は使用
        if use_cache and self.cached_trends and self.last_update:
            cache_age_minutes = (datetime.now() - self.last_update).total_seconds() / 60
            if cache_age_minutes < self.cache_valid_minutes:
                print(f"[トレンド取得] キャッシュから取得（{len(self.cached_trends)}件、{int(cache_age_minutes)}分前のデータ）")
                return self.cached_trends[:limit]
        
        # use_cache=False（手動更新）の場合はブラウザを表示しながらスクレイピング。
        # use_cache=True（バックグラウンド）ではヘッドレスで実行し、成功時のみキャッシュを更新。
        print("[トレンド取得] twittrend.jpから新規取得を開始..." + ("(ヘッドレス)" if use_cache else "(ブラウザ表示)"))
        headless = use_cache
        trends = await self._fetch_trends(limit, x_username, x_password, headless=headless)
        
        if trends:
            # 成功した場合のみキャッシュを更新
            self.cached_trends = trends
            self.last_update = datetime.now()
        else:
            print("[警告] トレンド取得に失敗したため、キャッシュを更新しません")
            # 失敗時はキャッシュを返す（無ければ空配列）
            return self.cached_trends[:limit] if self.cached_trends else []
        
        return trends[:limit]
    
    async def _fetch_trends(self, limit: int = 50, x_username: Optional[str] = None, x_password: Optional[str] = None, headless: bool = True) -> List[Dict[str, str]]:
        """
        twittrend.jpからトレンドを取得（Playwrightスクレイピング）
        
        Args:
            limit: 取得するトレンドの数
            x_username: 互換性のため残す（使用しない）
            x_password: 互換性のため残す（使用しない）
            headless: Trueの場合ヘッドレスモード（デフォルト: True）
        
        Returns:
            トレンドのリスト
        """
        try:
            # Playwrightでtwittrend.jpからスクレイピング
            if sys.platform == 'win32':
                loop = asyncio.get_event_loop()
                trends = await loop.run_in_executor(
                    self.executor,
                    self._scrape_trends_sync,
                    limit,
                    x_username,
                    x_password,
                    headless
                )
            else:
                trends = await self._scrape_trends_async(limit, x_username, x_password, headless=headless)
            
            if trends and len(trends) > 0:
                return trends
            
            # フォールバックデータを使用
            return self._get_fallback_trends(limit)
            
        except Exception as e:
            print(f"[エラー] トレンド取得: {str(e)}")
            return self._get_fallback_trends(limit)
    
    def _scrape_trends_sync(self, limit: int, x_username: Optional[str] = None, x_password: Optional[str] = None, headless: bool = True) -> List[Dict[str, str]]:
        """Windows環境用の同期スクレイピング（twittrend.jpから取得）"""
        trends: List[Dict[str, str]] = []
        try:
            print("[トレンドスクレイピング] twittrend.jpから取得開始...")
            with sync_playwright() as p:
                launch_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
                if not headless:
                    launch_args.append('--start-maximized')

                browser = p.chromium.launch(
                    headless=headless,
                    args=launch_args,
                    slow_mo=200 if not headless else 0
                )
                context = browser.new_context(
                    locale='ja-JP',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                if not headless:
                    try:
                        page.bring_to_front()
                        page.wait_for_timeout(1000)
                        print("[トレンドスクレイピング] ブラウザを前面に表示しました")
                    except Exception as e:
                        print(f"[警告] ブラウザの前面表示に失敗: {str(e)}")

                # twittrend.jpからトレンドを取得（ログイン不要）
                trending_url = "https://twittrend.jp/compare/result/23424856/1/"
                page.goto(trending_url, wait_until="networkidle", timeout=60000)
                if not headless:
                    page.wait_for_timeout(2000)
                page.wait_for_timeout(5000)  # ページ読み込み待機

                # テーブルからトレンドを抽出
                # テーブル構造: <table>内の<tr>要素からトレンドを取得
                trends = []
                try:
                    # テーブル行を取得（日本列のトレンド）
                    rows = page.query_selector_all('table tr')
                    print(f"[トレンドスクレイピング] テーブル行数: {len(rows)}")
                    
                    for row in rows[1:]:  # ヘッダー行をスキップ
                        try:
                            # 日本列（最初の列）のセルを取得
                            cells = row.query_selector_all('td')
                            if len(cells) >= 1:
                                # 最初のセル（日本列）からトレンドを抽出
                                cell_text = cells[0].inner_text().strip()
                                
                                # リンクからトレンドキーワードを取得
                                link = cells[0].query_selector('a[href*="twitter.com/search"]')
                                if link:
                                    link_text = link.inner_text().strip()
                                    # ハッシュタグや余分な文字を除去
                                    keyword = link_text.replace('#', '').strip()
                                    
                                    # ツイート数を取得（あれば）
                                    tweet_count = None
                                    tweet_count_text = cell_text
                                    if '件のツイート' in tweet_count_text:
                                        import re
                                        match = re.search(r'(\d+(?:,\d+)*)\s*件のツイート', tweet_count_text)
                                        if match:
                                            tweet_count_str = match.group(1).replace(',', '')
                                            try:
                                                tweet_count = int(tweet_count_str)
                                            except:
                                                pass
                                    
                                    if keyword and keyword not in [t['keyword'] for t in trends]:
                                        trends.append({
                                            "keyword": keyword,
                                            "tweet_count": tweet_count
                                        })
                                        print(f"[トレンドスクレイピング] トレンドを発見: {keyword} (ツイート数: {tweet_count})")
                                        
                                        if len(trends) >= limit:
                                            break
                        except Exception as e:
                            print(f"[警告] 行の処理中にエラー: {str(e)}")
                            continue
                    
                    # テーブルから取得できない場合は、リンクから直接取得
                    if len(trends) < limit:
                        links = page.query_selector_all('a[href*="twitter.com/search"]')
                        for link in links:
                            try:
                                keyword = link.inner_text().strip()
                                keyword = keyword.replace('#', '').strip()
                                
                                # スキップするテキストを除外
                                if not keyword or len(keyword) > 100:
                                    continue
                                if keyword in ['ツイート', 'Tweet', '検索', 'Search']:
                                    continue
                                
                                if keyword and keyword not in [t['keyword'] for t in trends]:
                                    trends.append({
                                        "keyword": keyword,
                                        "tweet_count": None
                                    })
                                    print(f"[トレンドスクレイピング] リンクからトレンドを発見: {keyword}")
                                    
                                    if len(trends) >= limit:
                                        break
                            except Exception:
                                continue
                
                except Exception as e:
                    print(f"[警告] テーブルからの取得に失敗: {str(e)}")
                    import traceback
                    print(traceback.format_exc())

                print(f"[トレンドスクレイピング] 完了: {len(trends)}件のトレンドを取得")

                browser.close()
        except Exception as e:
            print(f"[エラー] トレンドスクレイピング: {str(e)}")
            import traceback
            print(traceback.format_exc())

        return trends if trends else []
    
    async def _scrape_trends_async(self, limit: int, x_username: Optional[str] = None, x_password: Optional[str] = None, headless: bool = True) -> List[Dict[str, str]]:
        """非Windows環境用の非同期スクレイピング（twittrend.jpから取得）"""
        trends: List[Dict[str, str]] = []
        try:
            print("[トレンドスクレイピング] twittrend.jpから取得開始...")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context(
                    locale='ja-JP',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()

                # twittrend.jpからトレンドを取得（ログイン不要）
                trending_url = "https://twittrend.jp/compare/result/23424856/1/"
                await page.goto(trending_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)  # ページ読み込み待機

                # テーブルからトレンドを抽出
                trends = []
                try:
                    # テーブル行を取得（日本列のトレンド）
                    rows = await page.query_selector_all('table tr')
                    print(f"[トレンドスクレイピング] テーブル行数: {len(rows)}")
                    
                    for row in rows[1:]:  # ヘッダー行をスキップ
                        try:
                            # 日本列（最初の列）のセルを取得
                            cells = await row.query_selector_all('td')
                            if len(cells) >= 1:
                                # 最初のセル（日本列）からトレンドを抽出
                                cell_text = (await cells[0].inner_text()).strip()
                                
                                # リンクからトレンドキーワードを取得
                                link = await cells[0].query_selector('a[href*="twitter.com/search"]')
                                if link:
                                    link_text = (await link.inner_text()).strip()
                                    # ハッシュタグや余分な文字を除去
                                    keyword = link_text.replace('#', '').strip()
                                    
                                    # ツイート数を取得（あれば）
                                    tweet_count = None
                                    tweet_count_text = cell_text
                                    if '件のツイート' in tweet_count_text:
                                        import re
                                        match = re.search(r'(\d+(?:,\d+)*)\s*件のツイート', tweet_count_text)
                                        if match:
                                            tweet_count_str = match.group(1).replace(',', '')
                                            try:
                                                tweet_count = int(tweet_count_str)
                                            except:
                                                pass
                                    
                                    if keyword and keyword not in [t['keyword'] for t in trends]:
                                        trends.append({
                                            "keyword": keyword,
                                            "tweet_count": tweet_count
                                        })
                                        print(f"[トレンドスクレイピング] トレンドを発見: {keyword} (ツイート数: {tweet_count})")
                                        
                                        if len(trends) >= limit:
                                            break
                        except Exception as e:
                            print(f"[警告] 行の処理中にエラー: {str(e)}")
                            continue
                    
                    # テーブルから取得できない場合は、リンクから直接取得
                    if len(trends) < limit:
                        links = await page.query_selector_all('a[href*="twitter.com/search"]')
                        for link in links:
                            try:
                                keyword = (await link.inner_text()).strip()
                                keyword = keyword.replace('#', '').strip()
                                
                                # スキップするテキストを除外
                                if not keyword or len(keyword) > 100:
                                    continue
                                if keyword in ['ツイート', 'Tweet', '検索', 'Search']:
                                    continue
                                
                                if keyword and keyword not in [t['keyword'] for t in trends]:
                                    trends.append({
                                        "keyword": keyword,
                                        "tweet_count": None
                                    })
                                    print(f"[トレンドスクレイピング] リンクからトレンドを発見: {keyword}")
                                    
                                    if len(trends) >= limit:
                                        break
                            except Exception:
                                continue
                
                except Exception as e:
                    print(f"[警告] テーブルからの取得に失敗: {str(e)}")
                    import traceback
                    print(traceback.format_exc())

                print(f"[トレンドスクレイピング] 完了: {len(trends)}件のトレンドを取得")

                await browser.close()
        except Exception as e:
            print(f"[エラー] トレンドスクレイピング: {str(e)}")
            import traceback
            print(traceback.format_exc())

        return trends if trends else []
    
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
    
    def start_background_update(self, interval_minutes: int = 30):
        """
        バックグラウンドで定期的にトレンドを更新
        
        Args:
            interval_minutes: 更新間隔（分）
        """
        if self.is_background_running:
            print("[トレンド更新] 既にバックグラウンド更新が実行中です")
            return
        
        self.update_interval_minutes = interval_minutes
        self.is_background_running = True
        
        # 初回取得を実行
        def initial_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._update_trends_cache())
            finally:
                loop.close()
        
        initial_thread = threading.Thread(target=initial_update, daemon=True)
        initial_thread.start()
        
        # 定期更新をスケジュール
        schedule.clear()
        schedule.every(interval_minutes).minutes.do(
            lambda: self._run_update_in_thread()
        )
        
        def run_background():
            while self.is_background_running:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        self.background_thread = threading.Thread(target=run_background, daemon=True)
        self.background_thread.start()
        print(f"[トレンド更新] バックグラウンド更新を開始（{interval_minutes}分間隔）")
    
    def _run_update_in_thread(self):
        """別スレッドでトレンド更新を実行"""
        def update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._update_trends_cache())
            finally:
                loop.close()
        
        thread = threading.Thread(target=update, daemon=True)
        thread.start()
    
    async def _update_trends_cache(self):
        """トレンドを取得してキャッシュに保存"""
        try:
            print("[トレンド更新] バックグラウンドでトレンドを更新中...")
            trends = await self._fetch_trends(limit=50)
            self.cached_trends = trends
            self.last_update = datetime.now()
            print(f"[トレンド更新] キャッシュを更新しました（{len(trends)}件）")
        except Exception as e:
            print(f"[トレンド更新エラー] {str(e)}")
    
    def stop_background_update(self):
        """バックグラウンド更新を停止"""
        self.is_background_running = False
        schedule.clear()
        print("[トレンド更新] バックグラウンド更新を停止しました")
    
    def get_cache_info(self) -> Dict:
        """キャッシュ情報を取得"""
        return {
            "cached_count": len(self.cached_trends),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "is_background_running": self.is_background_running,
            "update_interval_minutes": self.update_interval_minutes
        }
