import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { generateCustomArticle, postDraft } from '../services/api';
import './CustomGenerator.css';

function CustomGenerator({ onLogout }) {
  const [customPrompt, setCustomPrompt] = useState('');
  const [llmProvider, setLlmProvider] = useState('openai');
  const [articleType, setArticleType] = useState('free'); // 'free' or 'paid'
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [posting, setPosting] = useState(false);

  const handleGenerate = async () => {
    if (!customPrompt.trim()) {
      setError('プロンプトを入力してください');
      return;
    }

    setError('');
    setLoading(true);
    setArticle(null);

    try {
      const result = await generateCustomArticle(customPrompt, llmProvider, articleType);
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
      await postDraft(article.id);
      alert('下書き投稿が完了しました！');
      setArticle(null);
      setCustomPrompt('');
    } catch (err) {
      alert('下書き投稿に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>カスタム生成</h2>
          <p style={{ marginBottom: '20px', color: '#666' }}>
            自由にプロンプトを入力して記事を生成できます。テーマ、内容、スタイルなどを自由に指定してください。
          </p>
          <div className="form-group">
            <label htmlFor="custom_prompt">プロンプト</label>
            <textarea
              id="custom_prompt"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="例: AIを活用した在宅副業について、初心者向けに分かりやすく説明する記事を作成してください。"
              rows={8}
              style={{ width: '100%', padding: '10px', fontSize: '14px', fontFamily: 'inherit' }}
            />
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
          <div className="form-group">
            <label>記事タイプ</label>
            <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  value="free"
                  checked={articleType === 'free'}
                  onChange={(e) => setArticleType(e.target.value)}
                  style={{ marginRight: '5px' }}
                />
                無料
              </label>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <input
                  type="radio"
                  value="paid"
                  checked={articleType === 'paid'}
                  onChange={(e) => setArticleType(e.target.value)}
                  style={{ marginRight: '5px' }}
                />
                有料
              </label>
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button
            onClick={handleGenerate}
            className="btn btn-primary"
            disabled={loading || !customPrompt.trim()}
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
                  rows={15}
                  style={{ width: '100%', padding: '10px', fontSize: '14px', fontFamily: 'inherit' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button
                  onClick={handlePostNow}
                  className="btn btn-success"
                  disabled={posting}
                >
                  {posting ? '投稿中...' : 'すぐに投稿'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CustomGenerator;

