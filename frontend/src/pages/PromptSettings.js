import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { getPromptSettings, updatePromptSettings } from '../services/api';
import './PromptSettings.css';

function PromptSettings({ onLogout }) {
  const [settings, setSettings] = useState({
    tone: '明るい',
    length: '2000-3000',
    other_conditions: '',
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getPromptSettings();
      setSettings(data);
    } catch (err) {
      console.error('プロンプト設定の取得に失敗しました:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setLoading(true);

    try {
      await updatePromptSettings(settings);
      setMessage('プロンプト設定を保存しました');
    } catch (err) {
      setMessage('設定の保存に失敗しました: ' + (err.response?.data?.detail || err.message));
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
          <h2>プロンプト調整</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="tone">文章の表現</label>
              <select id="tone" name="tone" value={settings.tone} onChange={handleChange}>
                <option value="明るい">明るい</option>
                <option value="丁寧">丁寧</option>
                <option value="フランク">フランク</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="length">文章の長さ</label>
              <select id="length" name="length" value={settings.length} onChange={handleChange}>
                <option value="1000-2000">1000-2000文字</option>
                <option value="2000-3000">2000-3000文字</option>
                <option value="3000-5000">3000-5000文字</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="other_conditions">その他条件</label>
              <textarea
                id="other_conditions"
                name="other_conditions"
                value={settings.other_conditions}
                onChange={handleChange}
                placeholder="追加の条件や指示を入力してください..."
                rows={5}
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

export default PromptSettings;

