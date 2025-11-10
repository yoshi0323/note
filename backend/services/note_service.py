"""
note.comへの下書き投稿サービス（ブラウザスクレイピング）
Windows環境ではsync_playwrightを使用してasyncio問題を回避
"""
from typing import Dict, Optional
import asyncio
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Windows環境ではsync_playwrightを使用
if sys.platform == 'win32':
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
    USE_SYNC = True
else:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    USE_SYNC = False

class NoteService:
    def __init__(self, note_id: str, note_password: str):
        self.note_id = note_id
        self.note_password = note_password
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.executor = ThreadPoolExecutor(max_workers=1) if USE_SYNC else None
    
    async def _init_browser(self, headless: bool = False):
        """ブラウザを初期化（Windows環境対応）"""
        try:
            if self.browser is None:
                print(f"[ブラウザ初期化] 開始 (headless={headless}, USE_SYNC={USE_SYNC})")
                
                if USE_SYNC:
                    # Windows環境: sync_playwrightを使用して別スレッドで実行
                    def init_sync():
                        p = sync_playwright().start()
                        browser = p.chromium.launch(
                            headless=headless,
                            args=[
                                '--disable-blink-features=AutomationControlled',
                                '--disable-dev-shm-usage',
                                '--no-sandbox'
                            ]
                        )
                        context = browser.new_context(
                            viewport={'width': 1920, 'height': 1080},
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            locale='ja-JP',
                            timezone_id='Asia/Tokyo'
                        )
                        page = context.new_page()
                        return p, browser, context, page
                    
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(self.executor, init_sync)
                    self.playwright, self.browser, self.context, self.page = result
                    print("[ブラウザ初期化] sync_playwrightで成功")
                else:
                    # 非Windows環境: async_playwrightを使用
                    self.playwright = await async_playwright().start()
                    self.browser = await self.playwright.chromium.launch(
                        headless=headless,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--no-sandbox'
                        ]
                    )
                    self.context = await self.browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='ja-JP',
                        timezone_id='Asia/Tokyo'
                    )
                    self.page = await self.context.new_page()
                    print("[ブラウザ初期化] async_playwrightで成功")
        except Exception as e:
            import traceback
            print(f"[ブラウザ初期化エラー] {str(e)}")
            print(f"[ブラウザ初期化エラー詳細] {traceback.format_exc()}")
            raise
    
    async def _close_browser(self):
        """ブラウザを閉じる"""
        try:
            if USE_SYNC:
                def close_sync():
                    if self.context:
                        self.context.close()
                    if self.browser:
                        self.browser.close()
                    if self.playwright:
                        self.playwright.stop()
                
                if self.playwright or self.browser or self.context:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(self.executor, close_sync)
            else:
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
            
            self.context = None
            self.browser = None
            self.playwright = None
            self.page = None
            print("[ブラウザ] 閉じました")
        except Exception as e:
            print(f"[ブラウザクローズエラー] {str(e)}")
    
    async def close(self):
        """ブラウザを閉じる（公開メソッド）"""
        await self._close_browser()
    
    async def login(self) -> bool:
        """
        noteにログイン（ブラウザスクレイピング）
        
        Returns:
            ログイン成功かどうか
        """
        try:
            # 本番環境（Renderなど）ではヘッドレスモードを使用
            import os
            render_env = os.getenv("RENDER")
            railway_env = os.getenv("RAILWAY")
            fly_env = os.getenv("FLY_APP_NAME")
            headless_env = os.getenv("HEADLESS_MODE")

            if headless_env is not None:
                headless_mode = headless_env.strip().lower() in ("1", "true", "yes", "on")
            else:
                headless_mode = any(flag is not None for flag in [render_env, railway_env, fly_env])

            print(f"[ログイン] headless_mode={headless_mode} (type={type(headless_mode)})")
            await self._init_browser(headless=headless_mode)
            
            if USE_SYNC:
                # Windows環境: 同期的に実行
                def login_sync():
                    page = self.page
                    page.goto('https://note.com/login', wait_until='domcontentloaded', timeout=30000)
                    time.sleep(3)
                    
                    page.screenshot(path='login_page.png')
                    print("[ログイン] ログインページのスクリーンショットを保存しました: login_page.png")
                    
                    # メールアドレス入力
                    email_filled = False
                    email_selectors = [
                        'input[type="email"]',
                        'input[name="email"]',
                        'input[placeholder*="メール"]',
                        'input[placeholder*="email"]',
                        'input[placeholder*="Email"]',
                        'input[id*="email"]',
                        'input[class*="email"]',
                        'input[type="text"]'
                    ]
                    
                    for selector in email_selectors:
                        try:
                            email_input = page.locator(selector).first
                            if email_input.count() > 0:
                                email_input.click()
                                time.sleep(0.5)
                                email_input.fill(self.note_id)
                                print(f"[ログイン] メールアドレスを入力しました (セレクター: {selector})")
                                email_filled = True
                                break
                        except Exception as e:
                            print(f"[ログイン] セレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not email_filled:
                        all_inputs = page.locator('input').all()
                        if len(all_inputs) > 0:
                            all_inputs[0].fill(self.note_id)
                            email_filled = True
                            print("[ログイン] 最初のinput要素にメールアドレスを入力しました")
                    
                    if not email_filled:
                        raise Exception("メールアドレス入力欄が見つかりませんでした")
                    
                    time.sleep(1)
                    
                    # パスワード入力
                    password_input = page.locator('input[type="password"]').first
                    if password_input.count() == 0:
                        raise Exception("パスワード入力欄が見つかりませんでした")
                    
                    password_input.click()
                    time.sleep(0.5)
                    password_input.fill(self.note_password)
                    print("[ログイン] パスワードを入力しました")
                    time.sleep(1)
                    
                    # ログインボタンをクリック
                    login_clicked = False
                    login_selectors = [
                        'button[type="submit"]',
                        'button:has-text("ログイン")',
                        'a:has-text("ログイン")',
                        'button.login',
                        'a.login',
                        '[class*="login"] button',
                        '[class*="Login"] button',
                        'form button',
                        'button:has-text("送信")',
                        'button:has-text("Sign in")'
                    ]
                    
                    for selector in login_selectors:
                        try:
                            login_button = page.locator(selector).first
                            if login_button.count() > 0:
                                login_button.click()
                                print(f"[ログイン] ログインボタンをクリックしました (セレクター: {selector})")
                                login_clicked = True
                                break
                        except Exception as e:
                            print(f"[ログイン] ログインボタンセレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not login_clicked:
                        page.keyboard.press('Enter')
                        print("[ログイン] Enterキーを押しました")
                    
                    time.sleep(5)
                    
                    page.screenshot(path='after_login.png')
                    print("[ログイン] ログイン後のスクリーンショットを保存しました: after_login.png")
                    
                    current_url = page.url
                    print(f"[ログイン] 現在のURL: {current_url}")
                    
                    if 'login' not in current_url.lower():
                        print("[ログイン] ログイン成功（URLが変更されました）")
                        return True
                    
                    success_indicators = [
                        'a[href*="/mypage"]',
                        'a[href*="/settings"]',
                        '[class*="mypage"]',
                        '[class*="user"]',
                        'button:has-text("投稿")',
                        'a:has-text("投稿")'
                    ]
                    
                    for indicator in success_indicators:
                        if page.locator(indicator).count() > 0:
                            print(f"[ログイン] ログイン成功（要素確認: {indicator}）")
                            return True
                    
                    error_selectors = [
                        '.error',
                        '.alert',
                        '[class*="error"]',
                        '[class*="Error"]',
                        '[role="alert"]'
                    ]
                    
                    for error_selector in error_selectors:
                        error_elements = page.locator(error_selector).all()
                        if len(error_elements) > 0:
                            try:
                                error_message = error_elements[0].inner_text()
                                if error_message:
                                    raise Exception(f"ログインエラー: {error_message}")
                            except:
                                pass
                    
                    print("[ログイン] ログイン状態を確認できませんでした")
                    return False
                
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self.executor, login_sync)
            else:
                # 非Windows環境: 非同期で実行
                print(f"[ログイン開始] note.comにアクセスします...")
                await self.page.goto('https://note.com/login', wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(3)
                
                await self.page.screenshot(path='login_page.png')
                print("[ログイン] ログインページのスクリーンショットを保存しました: login_page.png")
                
                email_filled = False
                email_selectors = [
                    'input[type="email"]',
                    'input[name="email"]',
                    'input[placeholder*="メール"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="Email"]',
                    'input[id*="email"]',
                    'input[class*="email"]',
                    'input[type="text"]'
                ]
                
                for selector in email_selectors:
                    try:
                        email_input = self.page.locator(selector).first
                        if await email_input.count() > 0:
                            await email_input.click()
                            await asyncio.sleep(0.5)
                            await email_input.fill(self.note_id)
                            print(f"[ログイン] メールアドレスを入力しました (セレクター: {selector})")
                            email_filled = True
                            break
                    except Exception as e:
                        print(f"[ログイン] セレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not email_filled:
                    all_inputs = await self.page.locator('input').all()
                    if len(all_inputs) > 0:
                        await all_inputs[0].fill(self.note_id)
                        email_filled = True
                        print("[ログイン] 最初のinput要素にメールアドレスを入力しました")
                
                if not email_filled:
                    raise Exception("メールアドレス入力欄が見つかりませんでした")
                
                await asyncio.sleep(1)
                
                password_input = self.page.locator('input[type="password"]').first
                if await password_input.count() == 0:
                    raise Exception("パスワード入力欄が見つかりませんでした")
                
                await password_input.click()
                await asyncio.sleep(0.5)
                await password_input.fill(self.note_password)
                print("[ログイン] パスワードを入力しました")
                await asyncio.sleep(1)
                
                login_clicked = False
                login_selectors = [
                    'button[type="submit"]',
                    'button:has-text("ログイン")',
                    'a:has-text("ログイン")',
                    'button.login',
                    'a.login',
                    '[class*="login"] button',
                    '[class*="Login"] button',
                    'form button',
                    'button:has-text("送信")',
                    'button:has-text("Sign in")'
                ]
                
                for selector in login_selectors:
                    try:
                        login_button = self.page.locator(selector).first
                        if await login_button.count() > 0:
                            await login_button.click()
                            print(f"[ログイン] ログインボタンをクリックしました (セレクター: {selector})")
                            login_clicked = True
                            break
                    except Exception as e:
                        print(f"[ログイン] ログインボタンセレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not login_clicked:
                    await self.page.keyboard.press('Enter')
                    print("[ログイン] Enterキーを押しました")
                
                await asyncio.sleep(5)
                
                await self.page.screenshot(path='after_login.png')
                print("[ログイン] ログイン後のスクリーンショットを保存しました: after_login.png")
                
                current_url = self.page.url
                print(f"[ログイン] 現在のURL: {current_url}")
                
                if 'login' not in current_url.lower():
                    print("[ログイン] ログイン成功（URLが変更されました）")
                    return True
                
                success_indicators = [
                    'a[href*="/mypage"]',
                    'a[href*="/settings"]',
                    '[class*="mypage"]',
                    '[class*="user"]',
                    'button:has-text("投稿")',
                    'a:has-text("投稿")'
                ]
                
                for indicator in success_indicators:
                    if await self.page.locator(indicator).count() > 0:
                        print(f"[ログイン] ログイン成功（要素確認: {indicator}）")
                        return True
                
                error_selectors = [
                    '.error',
                    '.alert',
                    '[class*="error"]',
                    '[class*="Error"]',
                    '[role="alert"]'
                ]
                
                for error_selector in error_selectors:
                    error_elements = await self.page.locator(error_selector).all()
                    if len(error_elements) > 0:
                        try:
                            error_message = await error_elements[0].inner_text()
                            if error_message:
                                raise Exception(f"ログインエラー: {error_message}")
                        except:
                            pass
                
                print("[ログイン] ログイン状態を確認できませんでした")
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ログインエラー] {error_msg}")
            try:
                if self.page:
                    if USE_SYNC:
                        self.page.screenshot(path=f'login_error_{int(time.time())}.png')
                    else:
                        await self.page.screenshot(path=f'login_error_{int(time.time())}.png')
            except:
                pass
            await self._close_browser()
            raise Exception(f"ログインに失敗しました: {error_msg}")
    
    async def post_draft(self, title: str, content: str) -> Dict[str, any]:
        """
        下書きを投稿（ブラウザスクレイピング）
        
        Args:
            title: 記事のタイトル
            content: 記事の本文
        
        Returns:
            投稿結果
        """
        try:
            # ログイン済みでない場合はログイン
            if self.page is None:
                print("[下書き投稿] ログインが必要です")
                if not await self.login():
                    raise Exception("ログインに失敗しました")
            elif USE_SYNC:
                # Windows環境: URLを同期的に確認
                def check_url():
                    return self.page.url
                loop = asyncio.get_event_loop()
                current_url = await loop.run_in_executor(self.executor, check_url)
                if 'login' in current_url.lower():
                    print("[下書き投稿] ログインが必要です")
                    if not await self.login():
                        raise Exception("ログインに失敗しました")
            else:
                current_url = self.page.url
                if 'login' in current_url.lower():
                    print("[下書き投稿] ログインが必要です")
                    if not await self.login():
                        raise Exception("ログインに失敗しました")
            
            if USE_SYNC:
                # Windows環境: 同期的に実行
                def post_draft_sync():
                    page = self.page
                    print(f"[下書き投稿] note.comのトップページに移動します...")
                    # まずトップページまたはマイページに移動
                    page.goto('https://note.com/', wait_until='domcontentloaded', timeout=30000)
                    time.sleep(3)
                    
                    # 「投稿」ボタンを探してクリック
                    print("[下書き投稿] 「投稿」ボタンを探します...")
                    post_button_clicked = False
                    post_button_selectors = [
                        'a:has-text("投稿")',
                        'button:has-text("投稿")',
                        'a[href*="/notes/new"]',
                        'a[href*="/mypage/notes/new"]',
                        '[class*="post"] a',
                        '[class*="Post"] a',
                        '[class*="投稿"]',
                        'a:has-text("新規投稿")',
                        'button:has-text("新規投稿")',
                        'a[href*="editor"]',
                        # 左上の投稿ボタン（より具体的なセレクター）
                        'header a:has-text("投稿")',
                        'nav a:has-text("投稿")',
                        '[role="navigation"] a:has-text("投稿")',
                        '.header a:has-text("投稿")',
                        '.nav a:has-text("投稿")'
                    ]
                    
                    for selector in post_button_selectors:
                        try:
                            post_button = page.locator(selector).first
                            if post_button.count() > 0:
                                post_button.click()
                                print(f"[下書き投稿] 「投稿」ボタンをクリックしました (セレクター: {selector})")
                                time.sleep(5)  # ページ遷移待機
                                post_button_clicked = True
                                break
                        except Exception as e:
                            print(f"[下書き投稿] 投稿ボタンセレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not post_button_clicked:
                        # 投稿ボタンが見つからない場合、直接URLにアクセスを試す
                        print("[下書き投稿] 「投稿」ボタンが見つからないため、直接URLにアクセスします...")
                        page.goto('https://note.com/mypage/notes/new', wait_until='domcontentloaded', timeout=30000)
                        time.sleep(5)
                    
                    # エディタページのURLを確認
                    current_url = page.url
                    print(f"[下書き投稿] 現在のURL: {current_url}")
                    
                    # エディタページでない場合、もう一度試す
                    if 'editor' not in current_url.lower() and '/notes/new' not in current_url.lower():
                        print("[下書き投稿] エディタページに遷移できていないため、再試行します...")
                        time.sleep(2)
                        # 再度投稿ボタンを探す
                        for selector in post_button_selectors[:5]:  # 主要なセレクターのみ
                            try:
                                post_button = page.locator(selector).first
                                if post_button.count() > 0:
                                    post_button.click()
                                    time.sleep(5)
                                    break
                            except:
                                continue
                    
                    time.sleep(3)  # エディタ読み込み待機
                    
                    page.screenshot(path='editor_page.png')
                    print("[下書き投稿] エディタページのスクリーンショットを保存しました: editor_page.png")
                    
                    # タイトル入力
                    print("[下書き投稿] タイトルを入力します...")
                    title_filled = False
                    title_selectors = [
                        'input[placeholder*="タイトル"]',
                        'input[placeholder*="title"]',
                        'input[placeholder*="Title"]',
                        'input[type="text"]',
                        'textarea[placeholder*="タイトル"]',
                        '[contenteditable="true"][placeholder*="タイトル"]',
                        '[contenteditable="true"][placeholder*="title"]',
                        '.note-editor-title',
                        '.editor-title',
                        '[class*="title"] input',
                        '[class*="Title"] input',
                        'input'
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_element = page.locator(selector).first
                            count = title_element.count()
                            if count > 0:
                                title_element.click()
                                time.sleep(0.5)
                                title_element.fill(title)
                                print(f"[下書き投稿] タイトルを入力しました (セレクター: {selector})")
                                title_filled = True
                                break
                        except Exception as e:
                            print(f"[下書き投稿] タイトルセレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not title_filled:
                        all_inputs = page.locator('input').all()
                        if len(all_inputs) > 0:
                            all_inputs[0].fill(title)
                            title_filled = True
                            print("[下書き投稿] 最初のinput要素にタイトルを入力しました")
                    
                    if not title_filled:
                        raise Exception("タイトル入力欄が見つかりませんでした")
                    
                    time.sleep(2)
                    
                    # 本文入力
                    print("[下書き投稿] 本文を入力します...")
                    content_filled = False
                    content_selectors = [
                        'textarea[placeholder*="本文"]',
                        'textarea[placeholder*="content"]',
                        'textarea[placeholder*="Content"]',
                        '[contenteditable="true"]',
                        'div[contenteditable="true"]',
                        'textarea',
                        '.note-editor-body',
                        '.editor-body',
                        '[class*="editor"] textarea',
                        '[class*="Editor"] textarea',
                        '[class*="editor"] [contenteditable]',
                        '[class*="Editor"] [contenteditable]'
                    ]
                    
                    for selector in content_selectors:
                        try:
                            content_element = page.locator(selector).first
                            count = content_element.count()
                            if count > 0:
                                content_element.click()
                                time.sleep(0.5)
                                
                                is_contenteditable = content_element.get_attribute('contenteditable')
                                if is_contenteditable:
                                    content_element.evaluate(f'element => element.innerHTML = `{content.replace(chr(10), "<br>")}`')
                                else:
                                    content_element.fill(content)
                                
                                print(f"[下書き投稿] 本文を入力しました (セレクター: {selector})")
                                content_filled = True
                                break
                        except Exception as e:
                            print(f"[下書き投稿] 本文セレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not content_filled:
                        all_textareas = page.locator('textarea, [contenteditable="true"]').all()
                        if len(all_textareas) > 0:
                            element = all_textareas[0]
                            is_contenteditable = element.get_attribute('contenteditable')
                            if is_contenteditable:
                                element.evaluate(f'element => element.innerHTML = `{content.replace(chr(10), "<br>")}`')
                            else:
                                element.fill(content)
                            content_filled = True
                            print("[下書き投稿] 最初のtextarea/contenteditable要素に本文を入力しました")
                    
                    if not content_filled:
                        raise Exception("本文入力欄が見つかりませんでした")
                    
                    time.sleep(3)
                    
                    page.screenshot(path='before_save.png')
                    print("[下書き投稿] 保存前のスクリーンショットを保存しました: before_save.png")
                    
                    # 保存ボタンをクリック
                    print("[下書き投稿] 下書き保存ボタンを探します...")
                    save_selectors = [
                        'button:has-text("下書き保存")',
                        'button:has-text("保存")',
                        'button:has-text("下書き")',
                        'button[type="submit"]',
                        'a:has-text("下書き保存")',
                        'a:has-text("保存")',
                        '.save-draft',
                        '.draft-save',
                        '[class*="save"] button',
                        '[class*="Save"] button',
                        'button:has-text("Save")',
                        '[data-testid*="save"]',
                        '[data-testid*="Save"]'
                    ]
                    
                    saved = False
                    for selector in save_selectors:
                        try:
                            save_button = page.locator(selector).first
                            if save_button.count() > 0:
                                save_button.click()
                                print(f"[下書き投稿] 保存ボタンをクリックしました (セレクター: {selector})")
                                time.sleep(5)
                                saved = True
                                break
                        except Exception as e:
                            print(f"[下書き投稿] 保存ボタンセレクター {selector} でエラー: {str(e)}")
                            continue
                    
                    if not saved:
                        print("[下書き投稿] 保存ボタンが見つからないため、Ctrl+Sを試します")
                        page.keyboard.press('Control+s')
                        time.sleep(3)
                    
                    time.sleep(3)
                    current_url = page.url
                    print(f"[下書き投稿] 保存後のURL: {current_url}")
                    
                    page.screenshot(path='after_save.png')
                    print("[下書き投稿] 保存後のスクリーンショットを保存しました: after_save.png")
                    
                    success = 'draft' in current_url.lower() or 'mypage' in current_url.lower() or 'note' in current_url.lower()
                    
                    if success:
                        print("[下書き投稿] 下書きを保存しました")
                        return {
                            "success": True,
                            "message": "下書きを保存しました",
                            "url": current_url
                        }
                    else:
                        error_elements = page.locator('.error, .alert, [class*="error"], [role="alert"]').all()
                        error_message = "不明なエラー"
                        if len(error_elements) > 0:
                            try:
                                error_message = error_elements[0].inner_text()
                            except:
                                pass
                        raise Exception(f"下書き保存に失敗しました: {error_message}")
                
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self.executor, post_draft_sync)
            else:
                # 非Windows環境: 非同期で実行
                print(f"[下書き投稿] note.comのトップページに移動します...")
                # まずトップページまたはマイページに移動
                await self.page.goto('https://note.com/', wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(3)
                
                # 「投稿」ボタンを探してクリック
                print("[下書き投稿] 「投稿」ボタンを探します...")
                post_button_clicked = False
                post_button_selectors = [
                    'a:has-text("投稿")',
                    'button:has-text("投稿")',
                    'a[href*="/notes/new"]',
                    'a[href*="/mypage/notes/new"]',
                    '[class*="post"] a',
                    '[class*="Post"] a',
                    '[class*="投稿"]',
                    'a:has-text("新規投稿")',
                    'button:has-text("新規投稿")',
                    'a[href*="editor"]',
                    # 左上の投稿ボタン（より具体的なセレクター）
                    'header a:has-text("投稿")',
                    'nav a:has-text("投稿")',
                    '[role="navigation"] a:has-text("投稿")',
                    '.header a:has-text("投稿")',
                    '.nav a:has-text("投稿")'
                ]
                
                for selector in post_button_selectors:
                    try:
                        post_button = self.page.locator(selector).first
                        if await post_button.count() > 0:
                            await post_button.click()
                            print(f"[下書き投稿] 「投稿」ボタンをクリックしました (セレクター: {selector})")
                            await asyncio.sleep(5)  # ページ遷移待機
                            post_button_clicked = True
                            break
                    except Exception as e:
                        print(f"[下書き投稿] 投稿ボタンセレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not post_button_clicked:
                    # 投稿ボタンが見つからない場合、直接URLにアクセスを試す
                    print("[下書き投稿] 「投稿」ボタンが見つからないため、直接URLにアクセスします...")
                    await self.page.goto('https://note.com/mypage/notes/new', wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(5)
                
                # エディタページのURLを確認
                current_url = self.page.url
                print(f"[下書き投稿] 現在のURL: {current_url}")
                
                # エディタページでない場合、もう一度試す
                if 'editor' not in current_url.lower() and '/notes/new' not in current_url.lower():
                    print("[下書き投稿] エディタページに遷移できていないため、再試行します...")
                    await asyncio.sleep(2)
                    # 再度投稿ボタンを探す
                    for selector in post_button_selectors[:5]:  # 主要なセレクターのみ
                        try:
                            post_button = self.page.locator(selector).first
                            if await post_button.count() > 0:
                                await post_button.click()
                                await asyncio.sleep(5)
                                break
                        except:
                            continue
                
                await asyncio.sleep(3)  # エディタ読み込み待機
                
                await self.page.screenshot(path='editor_page.png')
                print("[下書き投稿] エディタページのスクリーンショットを保存しました: editor_page.png")
                
                print("[下書き投稿] タイトルを入力します...")
                title_filled = False
                title_selectors = [
                    'input[placeholder*="タイトル"]',
                    'input[placeholder*="title"]',
                    'input[placeholder*="Title"]',
                    'input[type="text"]',
                    'textarea[placeholder*="タイトル"]',
                    '[contenteditable="true"][placeholder*="タイトル"]',
                    '[contenteditable="true"][placeholder*="title"]',
                    '.note-editor-title',
                    '.editor-title',
                    '[class*="title"] input',
                    '[class*="Title"] input',
                    'input'
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = self.page.locator(selector).first
                        count = await title_element.count()
                        if count > 0:
                            await title_element.click()
                            await asyncio.sleep(0.5)
                            await title_element.fill(title)
                            print(f"[下書き投稿] タイトルを入力しました (セレクター: {selector})")
                            title_filled = True
                            break
                    except Exception as e:
                        print(f"[下書き投稿] タイトルセレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not title_filled:
                    all_inputs = await self.page.locator('input').all()
                    if len(all_inputs) > 0:
                        await all_inputs[0].fill(title)
                        title_filled = True
                        print("[下書き投稿] 最初のinput要素にタイトルを入力しました")
                
                if not title_filled:
                    raise Exception("タイトル入力欄が見つかりませんでした")
                
                await asyncio.sleep(2)
                
                print("[下書き投稿] 本文を入力します...")
                content_filled = False
                content_selectors = [
                    'textarea[placeholder*="本文"]',
                    'textarea[placeholder*="content"]',
                    'textarea[placeholder*="Content"]',
                    '[contenteditable="true"]',
                    'div[contenteditable="true"]',
                    'textarea',
                    '.note-editor-body',
                    '.editor-body',
                    '[class*="editor"] textarea',
                    '[class*="Editor"] textarea',
                    '[class*="editor"] [contenteditable]',
                    '[class*="Editor"] [contenteditable]'
                ]
                
                for selector in content_selectors:
                    try:
                        content_element = self.page.locator(selector).first
                        count = await content_element.count()
                        if count > 0:
                            await content_element.click()
                            await asyncio.sleep(0.5)
                            
                            is_contenteditable = await content_element.get_attribute('contenteditable')
                            if is_contenteditable:
                                await content_element.evaluate(f'element => element.innerHTML = `{content.replace(chr(10), "<br>")}`')
                            else:
                                await content_element.fill(content)
                            
                            print(f"[下書き投稿] 本文を入力しました (セレクター: {selector})")
                            content_filled = True
                            break
                    except Exception as e:
                        print(f"[下書き投稿] 本文セレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not content_filled:
                    all_textareas = await self.page.locator('textarea, [contenteditable="true"]').all()
                    if len(all_textareas) > 0:
                        element = all_textareas[0]
                        is_contenteditable = await element.get_attribute('contenteditable')
                        if is_contenteditable:
                            await element.evaluate(f'element => element.innerHTML = `{content.replace(chr(10), "<br>")}`')
                        else:
                            await element.fill(content)
                        content_filled = True
                        print("[下書き投稿] 最初のtextarea/contenteditable要素に本文を入力しました")
                
                if not content_filled:
                    raise Exception("本文入力欄が見つかりませんでした")
                
                await asyncio.sleep(3)
                
                await self.page.screenshot(path='before_save.png')
                print("[下書き投稿] 保存前のスクリーンショットを保存しました: before_save.png")
                
                print("[下書き投稿] 下書き保存ボタンを探します...")
                save_selectors = [
                    'button:has-text("下書き保存")',
                    'button:has-text("保存")',
                    'button:has-text("下書き")',
                    'button[type="submit"]',
                    'a:has-text("下書き保存")',
                    'a:has-text("保存")',
                    '.save-draft',
                    '.draft-save',
                    '[class*="save"] button',
                    '[class*="Save"] button',
                    'button:has-text("Save")',
                    '[data-testid*="save"]',
                    '[data-testid*="Save"]'
                ]
                
                saved = False
                for selector in save_selectors:
                    try:
                        save_button = self.page.locator(selector).first
                        if await save_button.count() > 0:
                            await save_button.click()
                            print(f"[下書き投稿] 保存ボタンをクリックしました (セレクター: {selector})")
                            await asyncio.sleep(5)
                            saved = True
                            break
                    except Exception as e:
                        print(f"[下書き投稿] 保存ボタンセレクター {selector} でエラー: {str(e)}")
                        continue
                
                if not saved:
                    print("[下書き投稿] 保存ボタンが見つからないため、Ctrl+Sを試します")
                    await self.page.keyboard.press('Control+s')
                    await asyncio.sleep(3)
                
                await asyncio.sleep(3)
                current_url = self.page.url
                print(f"[下書き投稿] 保存後のURL: {current_url}")
                
                await self.page.screenshot(path='after_save.png')
                print("[下書き投稿] 保存後のスクリーンショットを保存しました: after_save.png")
                
                success = 'draft' in current_url.lower() or 'mypage' in current_url.lower() or 'note' in current_url.lower()
                
                if success:
                    print("[下書き投稿] 下書きを保存しました")
                    return {
                        "success": True,
                        "message": "下書きを保存しました",
                        "url": current_url
                    }
                else:
                    error_elements = await self.page.locator('.error, .alert, [class*="error"], [role="alert"]').all()
                    error_message = "不明なエラー"
                    if len(error_elements) > 0:
                        try:
                            error_message = await error_elements[0].inner_text()
                        except:
                            pass
                    raise Exception(f"下書き保存に失敗しました: {error_message}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"下書き投稿エラー: {error_msg}")
            try:
                if self.page:
                    if USE_SYNC:
                        self.page.screenshot(path=f'error_screenshot_{int(time.time())}.png')
                    else:
                        await self.page.screenshot(path=f'error_screenshot_{int(time.time())}.png')
            except:
                pass
            raise Exception(f"下書き投稿エラー: {error_msg}")
        finally:
            # ブラウザは閉じずに保持（次回の投稿で再利用可能）
            pass
