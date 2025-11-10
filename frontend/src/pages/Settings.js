import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { getSettings, updateSettings } from '../services/api';
import './Settings.css';

function Settings({ onLogout }) {
  const [settings, setSettings] = useState({
    note_id: '',
    note_password: '',
    openai_api_key: '',
    gemini_api_key: '',
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      console.error('設定の取得に失敗しました:', err);
      if (err.response?.status === 401) {
        // セッション切れ - ログイン画面にリダイレクト
        alert('セッションが切れました。再ログインしてください。');
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('session_id');
        window.location.href = '/login';
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setLoading(true);

    try {
      const result = await updateSettings(settings);
      setMessage('設定を保存しました');
      console.log('設定保存成功:', result);
    } catch (err) {
      console.error('設定保存エラー:', err);
      if (err.response?.status === 401) {
        setMessage('セッションが切れました。再ログインしてください。');
        setTimeout(() => {
          localStorage.removeItem('isAuthenticated');
          localStorage.removeItem('session_id');
          window.location.href = '/login';
        }, 2000);
      } else {
        setMessage('設定の保存に失敗しました: ' + (err.response?.data?.detail || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setSettings({
      ...settings,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>設定</h2>
          <div className="info-box">
            <p><strong>Note.com認証情報:</strong></p>
            <p>自動下書き投稿機能で使用されます。設定したID/パスワードで自動ログインし、記事を下書き保存します。</p>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="note_id">Note ID（メールアドレス）</label>
              <input
                type="email"
                id="note_id"
                name="note_id"
                value={settings.note_id}
                onChange={handleChange}
                placeholder="your-email@example.com"
              />
            </div>
            <div className="form-group">
              <label htmlFor="note_password">Note パスワード</label>
              <input
                type="password"
                id="note_password"
                name="note_password"
                value={settings.note_password}
                onChange={handleChange}
                placeholder="Noteのパスワード"
              />
            </div>
            <div className="form-group">
              <label htmlFor="openai_api_key">OpenAI API Key</label>
              <input
                type="password"
                id="openai_api_key"
                name="openai_api_key"
                value={settings.openai_api_key}
                onChange={handleChange}
                placeholder="sk-..."
              />
            </div>
            <div className="form-group">
              <label htmlFor="gemini_api_key">Gemini API Key</label>
              <input
                type="password"
                id="gemini_api_key"
                name="gemini_api_key"
                value={settings.gemini_api_key}
                onChange={handleChange}
                placeholder="Gemini API Key"
              />
            </div>
            {message && (
              <div className={message.includes('失敗') ? 'error' : 'success'}>
                {message}
              </div>
            )}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Settings;

