import React, { useState } from 'react';
import './ScheduleManager.css';

const DAYS_OF_WEEK = [
  { value: 0, label: '月曜日' },
  { value: 1, label: '火曜日' },
  { value: 2, label: '水曜日' },
  { value: 3, label: '木曜日' },
  { value: 4, label: '金曜日' },
  { value: 5, label: '土曜日' },
  { value: 6, label: '日曜日' }
];

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const MINUTES = [0, 15, 30, 45];

function ScheduleManager({ schedules, onAddSchedule, onDeleteSchedule, articleId, theme, trendKeyword, llmProvider }) {
  const [scheduleType, setScheduleType] = useState('daily');
  const [dayOfWeek, setDayOfWeek] = useState(null);
  const [hour, setHour] = useState(12);
  const [minute, setMinute] = useState(0);
  const [showAddForm, setShowAddForm] = useState(false);

  const handleAddSchedule = () => {
    if (scheduleType === 'weekly' && dayOfWeek === null) {
      alert('曜日を選択してください');
      return;
    }

    const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
    
    onAddSchedule({
      schedule_type: scheduleType,
      day_of_week: scheduleType === 'weekly' ? dayOfWeek : null,
      time: timeStr,
      article_id: articleId || null,
      theme: theme || null,
      trend_keyword: trendKeyword || null,
      llm_provider: llmProvider || 'openai'
    });

    // フォームをリセット
    setScheduleType('daily');
    setDayOfWeek(null);
    setHour(12);
    setMinute(0);
    setShowAddForm(false);
  };

  const formatScheduleDisplay = (schedule) => {
    let timeStr = '';
    if (schedule.schedule_type === 'daily') {
      timeStr = `毎日 ${schedule.time}`;
    } else {
      const dayLabel = DAYS_OF_WEEK.find(d => d.value === schedule.day_of_week)?.label || '';
      timeStr = `${dayLabel} ${schedule.time}`;
    }
    
    // トレンドとテーマの情報を追加
    const parts = [timeStr, '有効'];
    if (schedule.trend_keyword) {
      parts.push(`トレンド: ${schedule.trend_keyword}`);
    }
    if (schedule.theme) {
      parts.push(`テーマ: ${schedule.theme}`);
    }
    
    return parts.join(' ');
  };

  return (
    <div className="schedule-manager">
      <h3>スケジュール投稿設定</h3>
      
      {schedules && schedules.length > 0 && (
        <div className="schedules-list">
          <h4>登録済みスケジュール</h4>
          {schedules.map((schedule) => (
            <div key={schedule.schedule_id} className="schedule-item">
              <div className="schedule-info">
                <span className="schedule-display">{formatScheduleDisplay(schedule)}</span>
              </div>
              <button
                onClick={() => onDeleteSchedule(schedule.schedule_id)}
                className="btn btn-danger btn-small"
              >
                削除
              </button>
            </div>
          ))}
        </div>
      )}

      {!showAddForm ? (
        <button
          onClick={() => setShowAddForm(true)}
          className="btn btn-secondary"
        >
          + スケジュールを追加
        </button>
      ) : (
        <div className="schedule-form">
          <div className="form-group">
            <label>スケジュールタイプ</label>
            <select
              value={scheduleType}
              onChange={(e) => {
                setScheduleType(e.target.value);
                if (e.target.value === 'daily') {
                  setDayOfWeek(null);
                }
              }}
            >
              <option value="daily">毎日</option>
              <option value="weekly">特定の曜日</option>
            </select>
          </div>

          {scheduleType === 'weekly' && (
            <div className="form-group">
              <label>曜日を選択</label>
              <select
                value={dayOfWeek !== null ? dayOfWeek : ''}
                onChange={(e) => setDayOfWeek(parseInt(e.target.value))}
              >
                <option value="">曜日を選択してください</option>
                {DAYS_OF_WEEK.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label>時刻</label>
            <div className="time-selector">
              <select
                value={hour}
                onChange={(e) => setHour(parseInt(e.target.value))}
              >
                {HOURS.map((h) => (
                  <option key={h} value={h}>
                    {String(h).padStart(2, '0')}時
                  </option>
                ))}
              </select>
              <span>：</span>
              <select
                value={minute}
                onChange={(e) => setMinute(parseInt(e.target.value))}
              >
                {MINUTES.map((m) => (
                  <option key={m} value={m}>
                    {String(m).padStart(2, '0')}分
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="schedule-form-actions">
            <button
              onClick={handleAddSchedule}
              className="btn btn-primary"
              disabled={scheduleType === 'weekly' && dayOfWeek === null}
            >
              スケジュールを追加
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                setScheduleType('daily');
                setDayOfWeek(null);
                setHour(12);
                setMinute(0);
              }}
              className="btn btn-secondary"
            >
              キャンセル
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScheduleManager;

