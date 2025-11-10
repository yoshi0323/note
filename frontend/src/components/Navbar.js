import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

function Navbar({ onLogout }) {
  const location = useLocation();

  return (
    <div className="navbar">
      <h1>Note下書き投稿システム</h1>
      <nav>
        <Link to="/dashboard" className={location.pathname === '/dashboard' ? 'active' : ''}>
          ダッシュボード
        </Link>
        <Link to="/theme-generator" className={location.pathname === '/theme-generator' ? 'active' : ''}>
          テーマ生成
        </Link>
        <Link to="/trend-generator" className={location.pathname === '/trend-generator' ? 'active' : ''}>
          トレンド生成
        </Link>
        <Link to="/manual-editor" className={location.pathname === '/manual-editor' ? 'active' : ''}>
          手動編集
        </Link>
        <Link to="/custom-generator" className={location.pathname === '/custom-generator' ? 'active' : ''}>
          カスタム生成
        </Link>
        <Link to="/prompt-settings" className={location.pathname === '/prompt-settings' ? 'active' : ''}>
          プロンプト設定
        </Link>
        <Link to="/settings" className={location.pathname === '/settings' ? 'active' : ''}>
          設定
        </Link>
        <button onClick={onLogout || (() => {
          localStorage.removeItem('isAuthenticated');
          localStorage.removeItem('session_id');
          window.location.href = '/login';
        })} className="btn-logout">
          ログアウト
        </button>
      </nav>
    </div>
  );
}

export default Navbar;

