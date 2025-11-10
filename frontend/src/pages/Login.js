import React, { useState } from 'react';
import { login } from '../services/api';
import './Login.css';

function Login({ onLogin }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(password);
      if (result.success) {
        onLogin(result.session_id);
      }
    } catch (err) {
      console.error('ログインエラー詳細:', err);
      // ネットワークエラーの場合の詳細なメッセージ
      if (err.code === 'ERR_NETWORK' || err.message?.includes('ERR_BLOCKED_BY_CLIENT')) {
        setError('バックエンドサーバーに接続できません。サーバーが起動しているか、ブラウザの拡張機能（広告ブロッカーなど）がリクエストをブロックしていないか確認してください。');
      } else {
        setError(err.response?.data?.detail || 'ログインに失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Note下書き投稿システム</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="password">パスワード</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="パスワードを入力"
              required
            />
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;

