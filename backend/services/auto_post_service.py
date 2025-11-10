"""
自動投稿サービス（複数スケジュール対応、曜日ベース）
"""
import schedule
import time
import threading
from typing import Dict, Callable, List, Optional
from datetime import datetime
import asyncio

class AutoPostService:
    def __init__(self):
        self.scheduled_posts = []  # スケジュール済み投稿のリスト
        self.callbacks = {}  # スケジュールID -> コールバック関数のマッピング
        self.is_running = False
        self.scheduler_thread = None
    
    def add_schedule(
        self,
        schedule_id: str,
        article_id: int,
        schedule_type: str,  # "daily", "weekly"
        day_of_week: Optional[int] = None,  # 0=月曜日, 6=日曜日
        time_str: str = "12:00",  # HH:MM形式
        post_callback: Optional[Callable] = None
    ) -> Dict:
        """
        スケジュールを追加
        
        Args:
            schedule_id: スケジュールID（一意）
            article_id: 記事ID
            schedule_type: "daily"（毎日）または "weekly"（週次）
            day_of_week: 曜日（0=月曜日, 1=火曜日, ..., 6=日曜日、weeklyの場合のみ）
            time_str: 時刻（HH:MM形式）
            post_callback: 投稿実行時のコールバック関数
        
        Returns:
            スケジュール情報
        """
        try:
            # 時刻の形式を確認
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("時刻の形式が正しくありません（HH:MM形式で0-23時、0-59分）")
            
            schedule_info = {
                "schedule_id": schedule_id,
                "article_id": article_id,
                "schedule_type": schedule_type,
                "day_of_week": day_of_week,
                "time": time_str,
                "status": "active",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # scheduleライブラリに登録
            if schedule_type == "daily":
                # 毎日
                schedule.every().day.at(time_str).do(
                    self._execute_post,
                    schedule_id=schedule_id,
                    article_id=article_id,
                    post_callback=post_callback
                )
            elif schedule_type == "weekly":
                # 特定の曜日
                if day_of_week is None:
                    raise ValueError("週次の場合は曜日を指定してください")
                
                days = {
                    0: schedule.every().monday,
                    1: schedule.every().tuesday,
                    2: schedule.every().wednesday,
                    3: schedule.every().thursday,
                    4: schedule.every().friday,
                    5: schedule.every().saturday,
                    6: schedule.every().sunday
                }
                
                if day_of_week not in days:
                    raise ValueError("曜日は0（月曜日）から6（日曜日）の範囲で指定してください")
                
                days[day_of_week].at(time_str).do(
                    self._execute_post,
                    schedule_id=schedule_id,
                    article_id=article_id,
                    post_callback=post_callback
                )
            else:
                raise ValueError("schedule_typeは'daily'または'weekly'である必要があります")
            
            # スケジュールリストに追加
            self.scheduled_posts.append(schedule_info)
            
            # コールバック関数を保存
            if post_callback:
                self.callbacks[schedule_id] = post_callback
            
            # スケジューラーが起動していない場合は起動
            if not self.is_running:
                self.start()
            
            print(f"[スケジュール追加] スケジュールID {schedule_id} を追加しました（{schedule_type}, {time_str}）")
            return schedule_info
        except Exception as e:
            raise Exception(f"スケジュール設定エラー: {str(e)}")
    
    def remove_schedule(self, schedule_id: str):
        """スケジュールを削除"""
        # スケジュールリストから削除
        removed_schedule = next((s for s in self.scheduled_posts if s.get("schedule_id") == schedule_id), None)
        self.scheduled_posts = [s for s in self.scheduled_posts if s.get("schedule_id") != schedule_id]
        
        # コールバック関数を削除
        if schedule_id in self.callbacks:
            del self.callbacks[schedule_id]
        
        # scheduleライブラリから削除（全クリアして再登録）
        schedule.clear()
        
        # 残りのスケジュールを再登録（コールバック関数を保持）
        for schedule_info in self.scheduled_posts:
            if schedule_info.get("status") == "active":
                post_callback = self.callbacks.get(schedule_info["schedule_id"])
                if schedule_info["schedule_type"] == "daily":
                    schedule.every().day.at(schedule_info["time"]).do(
                        self._execute_post,
                        schedule_id=schedule_info["schedule_id"],
                        article_id=schedule_info.get("article_id", 0),
                        post_callback=post_callback
                    )
                elif schedule_info["schedule_type"] == "weekly":
                    day_of_week = schedule_info.get("day_of_week")
                    if day_of_week is not None:
                        days = {
                            0: schedule.every().monday,
                            1: schedule.every().tuesday,
                            2: schedule.every().wednesday,
                            3: schedule.every().thursday,
                            4: schedule.every().friday,
                            5: schedule.every().saturday,
                            6: schedule.every().sunday
                        }
                        if day_of_week in days:
                            days[day_of_week].at(schedule_info["time"]).do(
                                self._execute_post,
                                schedule_id=schedule_info["schedule_id"],
                                article_id=schedule_info.get("article_id", 0),
                                post_callback=post_callback
                            )
        
        print(f"[スケジュール削除] スケジュールID {schedule_id} を削除しました（残り: {len(self.scheduled_posts)}件）")
    
    def _execute_post(self, schedule_id: str, article_id: int, post_callback: Optional[Callable] = None):
        """投稿を実行"""
        try:
            print(f"[スケジュール実行] スケジュールID {schedule_id} を実行します")
            if post_callback:
                # コールバックがasync関数かどうかを確認
                if asyncio.iscoroutinefunction(post_callback):
                    # 新しいイベントループを作成して実行
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(post_callback())
                        print(f"[スケジュール実行] スケジュールID {schedule_id} の実行が完了しました")
                    finally:
                        loop.close()
                else:
                    post_callback()
                    print(f"[スケジュール実行] スケジュールID {schedule_id} の実行が完了しました")
            else:
                print(f"[スケジュール実行警告] スケジュールID {schedule_id} にコールバックが設定されていません")
            
            # スケジュール済み投稿のステータスを更新
            for post in self.scheduled_posts:
                if post.get("schedule_id") == schedule_id:
                    post["last_executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
        except Exception as e:
            print(f"[自動投稿エラー] スケジュールID {schedule_id}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def start(self):
        """スケジューラーを開始"""
        if self.is_running:
            return
        
        self.is_running = True
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("[スケジューラー] 開始しました")
    
    def stop(self):
        """スケジューラーを停止"""
        self.is_running = False
        schedule.clear()
        print("[スケジューラー] 停止しました")
    
    def get_scheduled_posts(self) -> List[Dict]:
        """スケジュール済み投稿の一覧を取得"""
        return self.scheduled_posts
