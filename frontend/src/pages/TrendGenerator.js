import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import ScheduleManager from '../components/ScheduleManager';
import { getThemes, getTrends, generateTrendArticle, postDraft, getSchedules, addSchedule, deleteSchedule } from '../services/api';
import './TrendGenerator.css';

function TrendGenerator({ onLogout }) {
  const [themes, setThemes] = useState([]);
  const [trends, setTrends] = useState([]);
  const [selectedTheme, setSelectedTheme] = useState('');
  const [selectedTrend, setSelectedTrend] = useState('');
  const [llmProvider, setLlmProvider] = useState('openai');
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingTrends, setLoadingTrends] = useState(false);
  const [error, setError] = useState('');
  const [schedules, setSchedules] = useState([]);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadThemes();
    loadTrends();
  }, []);

  const loadThemes = async () => {
    try {
      const data = await getThemes();
      setThemes(data.themes || []);
    } catch (err) {
      console.error('テーマの取得に失敗しました:', err);
    }
  };

  const loadTrends = async () => {
    setLoadingTrends(true);
    try {
      const data = await getTrends(10);
      setTrends(data.trends || []);
    } catch (err) {
      console.error('トレンドの取得に失敗しました:', err);
    } finally {
      setLoadingTrends(false);
    }
  };

  const loadSchedules = async () => {
    try {
      const data = await getSchedules();
      // このテーマとトレンドに関連するスケジュールのみをフィルタリング
      const relatedSchedules = (data.schedules || []).filter(
        s => s.theme === selectedTheme && s.trend_keyword === selectedTrend && !s.article_id
      );
      setSchedules(relatedSchedules);
    } catch (err) {
      console.error('スケジュールの取得に失敗しました:', err);
    }
  };

  const handleGenerate = async () => {
    if (!selectedTheme || !selectedTrend) {
      setError('テーマとトレンドを選択してください');
      return;
    }

    setError('');
    setLoading(true);
    setArticle(null);

    try {
      const result = await generateTrendArticle(selectedTheme, selectedTrend, llmProvider);
      if (result.success) {
        setArticle(result.article);
      }
    } catch (err) {
      setError(err.response?.data?.detail || '記事の生成に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handlePostNow = async () => {
    if (!article || !article.id) {
      alert('まず記事を生成してください');
      return;
    }

    if (!window.confirm('この記事をnote.comに下書き投稿しますか？')) {
      return;
    }

    setPosting(true);
    try {
      const result = await postDraft(article.id, null);
      if (result.success) {
        alert('下書きを投稿しました！');
        // 記事を再読み込み（postedフラグ更新のため）
        await loadThemes();
      }
    } catch (err) {
      alert('投稿に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPosting(false);
    }
  };

  const handleAddSchedule = async (scheduleData) => {
    try {
      const result = await addSchedule({
        ...scheduleData,
        theme: selectedTheme,
        trend_keyword: selectedTrend,
        llm_provider: llmProvider
      });
      if (result.success) {
        alert('スケジュールを追加しました');
        await loadSchedules();
      }
    } catch (err) {
      alert('スケジュールの追加に失敗しました: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteSchedule = async (scheduleId) => {
    if (!window.confirm('このスケジュールを削除しますか？')) {
      return;
    }

    try {
      const result = await deleteSchedule(scheduleId);
      if (result.success) {
        alert('スケジュールを削除しました');
        await loadSchedules();
      }
    } catch (err) {
      alert('スケジュールの削除に失敗しました: ' + (err.response?.data?.detail || err.message));
    }
  };

  useEffect(() => {
    if (selectedTheme && selectedTrend) {
      loadSchedules();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTheme, selectedTrend]);

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>Xトレンド記事生成</h2>
          <div className="form-group">
            <label htmlFor="trend">トレンドを選択</label>
            {loadingTrends ? (
              <p>トレンドを取得中...</p>
            ) : (
              <select
                id="trend"
                value={selectedTrend}
                onChange={(e) => setSelectedTrend(e.target.value)}
              >
                <option value="">トレンドを選択してください</option>
                {trends.map((trend, index) => (
                  <option key={index} value={trend.keyword}>
                    {trend.keyword} ({trend.tweet_count?.toLocaleString()}ツイート)
                  </option>
                ))}
              </select>
            )}
            <button
              type="button"
              onClick={loadTrends}
              className="btn btn-secondary"
              style={{ marginTop: '10px' }}
            >
              トレンドを更新
            </button>
          </div>
          <div className="form-group">
            <label htmlFor="theme">テーマを選択</label>
            <select
              id="theme"
              value={selectedTheme}
              onChange={(e) => setSelectedTheme(e.target.value)}
            >
              <option value="">テーマを選択してください</option>
              {themes.map((theme) => (
                <option key={theme} value={theme}>
                  {theme}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="llm_provider">LLMプロバイダー</label>
            <select
              id="llm_provider"
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
            >
              <option value="openai">OpenAI</option>
              <option value="gemini">Gemini</option>
            </select>
          </div>
          {error && <div className="error">{error}</div>}
          <button
            onClick={handleGenerate}
            className="btn btn-primary"
            disabled={loading || !selectedTheme || !selectedTrend}
          >
            {loading ? '生成中...' : '記事を生成'}
          </button>
          {article && (
            <div className="article-result">
              <h3>生成された記事</h3>
              <div className="form-group">
                <label>タイトル</label>
                <input type="text" value={article.title} readOnly />
              </div>
              <div className="form-group">
                <label>本文</label>
                <textarea
                  value={article.content}
                  readOnly
                  rows={20}
                  style={{ minHeight: '400px' }}
                />
              </div>
              <div className="button-group" style={{ marginTop: '20px' }}>
                <button
                  onClick={handlePostNow}
                  className="btn btn-primary"
                  disabled={posting}
                >
                  {posting ? '投稿中...' : '今すぐ投稿(自動でブラウザ操作)'}
                </button>
              </div>
            </div>
          )}
          
          {selectedTheme && selectedTrend && (
            <ScheduleManager
              schedules={schedules}
              onAddSchedule={handleAddSchedule}
              onDeleteSchedule={handleDeleteSchedule}
              theme={selectedTheme}
              trendKeyword={selectedTrend}
              llmProvider={llmProvider}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default TrendGenerator;
