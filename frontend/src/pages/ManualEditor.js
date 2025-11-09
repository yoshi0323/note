import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { generateManualArticle } from '../services/api';
import './ManualEditor.css';

function ManualEditor({ onLogout }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [theme, setTheme] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !content) {
      setMessage('タイトルと本文を入力してください');
      return;
    }

    setMessage('');
    setLoading(true);

    try {
      const result = await generateManualArticle({
        title,
        content,
        theme: theme || null,
      });
      if (result.success) {
        setMessage('記事を保存しました');
        // オプション: フォームをクリア
        // setTitle('');
        // setContent('');
        // setTheme('');
      }
    } catch (err) {
      setMessage('記事の保存に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>手動記事編集</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="title">タイトル</label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="記事のタイトル"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="theme">テーマ（任意）</label>
              <input
                type="text"
                id="theme"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="テーマ"
              />
            </div>
            <div className="form-group">
              <label htmlFor="content">本文（2000-3000文字推奨）</label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="記事の本文を入力してください..."
                rows={30}
                required
                style={{ minHeight: '500px' }}
              />
              <p className="char-count">文字数: {content.length}</p>
            </div>
            {message && (
              <div className={message.includes('失敗') ? 'error' : 'success'}>
                {message}
              </div>
            )}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : '記事を保存'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ManualEditor;

