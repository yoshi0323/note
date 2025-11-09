import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { getArticles, postDraft, generateXPost } from '../services/api';
import './AutoPost.css';

function AutoPost({ onLogout }) {
  const [articles, setArticles] = useState([]);
  const [selectedArticleId, setSelectedArticleId] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [xPost, setXPost] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      const data = await getArticles();
      setArticles(data.articles || []);
    } catch (err) {
      console.error('記事の取得に失敗しました:', err);
    }
  };

  const handlePost = async (immediate = false) => {
    if (!selectedArticleId) {
      setMessage('記事を選択してください');
      return;
    }

    if (!immediate && !scheduledTime) {
      setMessage('投稿時刻を設定してください（即座に投稿する場合は「今すぐ投稿」ボタンを使用）');
      return;
    }

    setMessage('');
    setLoading(true);

    try {
      const result = await postDraft(
        parseInt(selectedArticleId),
        immediate ? null : scheduledTime
      );
      if (result.success) {
        if (immediate) {
          setMessage(result.message || '下書きを保存しました！ブラウザで自動投稿が完了しました。');
          setScheduledTime('');
        } else {
          setMessage(result.message || '投稿をスケジュールしました');
        }
      }
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      setMessage('投稿に失敗しました: ' + errorDetail);
      console.error('投稿エラー:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateXPost = async () => {
    if (!selectedArticleId) {
      setMessage('記事を選択してください');
      return;
    }

    setMessage('');
    setLoading(true);

    try {
      const result = await generateXPost(parseInt(selectedArticleId));
      if (result.success) {
        setXPost(result.x_post);
      }
    } catch (err) {
      setMessage('X投稿文の生成に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>自動下書き投稿</h2>
          <div className="info-box">
            <p><strong>使い方:</strong></p>
            <ol>
              <li>設定画面でnote.comのID/パスワードを設定してください</li>
              <li>記事を選択して「今すぐ投稿」ボタンをクリック</li>
              <li>自動でブラウザが開き、ログイン→タイトル/本文入力→下書き保存が実行されます</li>
            </ol>
          </div>
          <div className="form-group">
            <label htmlFor="article">記事を選択</label>
            <select
              id="article"
              value={selectedArticleId}
              onChange={(e) => setSelectedArticleId(e.target.value)}
            >
              <option value="">記事を選択してください</option>
              {articles.map((article) => (
                <option key={article.id} value={article.id}>
                  {article.title}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="scheduled_time">投稿時刻（YYYY-MM-DD HH:MM形式、スケジュール投稿の場合）</label>
            <input
              type="text"
              id="scheduled_time"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              placeholder="2024-01-01 12:00"
            />
            <small>例: 2024-01-01 12:00（スケジュール投稿の場合のみ必要）</small>
          </div>
          {message && (
            <div className={message.includes('失敗') || message.includes('エラー') ? 'error' : 'success'}>
              {message}
            </div>
          )}
          {loading && (
            <div className="loading-box">
              <p>⏳ ブラウザで自動投稿を実行中...</p>
              <p className="loading-note">（ヘッドレスモードで実行されます）</p>
            </div>
          )}
          <div className="button-group">
            <button
              onClick={() => handlePost(false)}
              className="btn btn-primary"
              disabled={loading || !selectedArticleId || !scheduledTime}
            >
              {loading ? '処理中...' : 'スケジュール投稿'}
            </button>
            <button
              onClick={() => handlePost(true)}
              className="btn btn-secondary"
              disabled={loading || !selectedArticleId}
            >
              {loading ? '投稿中...' : '今すぐ投稿（自動でブラウザ操作）'}
            </button>
          </div>
          <div style={{ marginTop: '30px', paddingTop: '30px', borderTop: '2px solid #ddd' }}>
            <h3>X投稿用本文生成</h3>
            <button
              onClick={handleGenerateXPost}
              className="btn btn-primary"
              disabled={loading || !selectedArticleId}
            >
              {loading ? '生成中...' : 'X投稿文を生成'}
            </button>
            {xPost && (
              <div className="x-post-result">
                <div className="form-group">
                  <label>投稿文</label>
                  <textarea
                    value={xPost.full_post}
                    readOnly
                    rows={5}
                    style={{ minHeight: '100px' }}
                  />
                </div>
                {xPost.hashtags && xPost.hashtags.length > 0 && (
                  <div>
                    <label>ハッシュタグ</label>
                    <p>{xPost.hashtags.join(', ')}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AutoPost;

