import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { getArticles, postDraft, deleteArticle } from '../services/api';
import './Dashboard.css';

function Dashboard({ onLogout }) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedArticles, setExpandedArticles] = useState({});
  const [postingArticles, setPostingArticles] = useState({});

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      const data = await getArticles();
      setArticles(data.articles || []);
    } catch (err) {
      console.error('記事の取得に失敗しました:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (articleId) => {
    setExpandedArticles(prev => ({
      ...prev,
      [articleId]: !prev[articleId]
    }));
  };

  const handlePost = async (articleId) => {
    if (!window.confirm('この記事をnote.comに下書き投稿しますか？')) {
      return;
    }

    setPostingArticles(prev => ({ ...prev, [articleId]: true }));

    try {
      const result = await postDraft(articleId, null);
      if (result.success) {
        alert('下書きを投稿しました！');
        // 記事一覧を再読み込み
        await loadArticles();
      }
    } catch (err) {
      alert('投稿に失敗しました: ' + (err.response?.data?.detail || err.message));
    } finally {
      setPostingArticles(prev => ({ ...prev, [articleId]: false }));
    }
  };

  const handleDelete = async (articleId) => {
    if (!window.confirm('この記事を削除しますか？')) {
      return;
    }

    try {
      const result = await deleteArticle(articleId);
      if (result.success) {
        alert('記事を削除しました');
        // 記事一覧を再読み込み
        await loadArticles();
      }
    } catch (err) {
      alert('削除に失敗しました: ' + (err.response?.data?.detail || err.message));
    }
  };

  const cleanTitle = (title) => {
    // Markdown記号を削除
    return title.replace(/^#+\s*/, '').trim();
  };

  const cleanContent = (content) => {
    // Markdown記号を削除
    let cleaned = content.replace(/^#+\s*/gm, ''); // 見出し記号を削除
    cleaned = cleaned.replace(/\*\*/g, ''); // 太字記号を削除
    cleaned = cleaned.replace(/\*/g, ''); // リスト記号を削除
    return cleaned.trim();
  };

  return (
    <div className="App">
      <Navbar onLogout={onLogout} />
      <div className="container">
        <div className="card">
          <h2>ダッシュボード</h2>
          {loading ? (
            <p>読み込み中...</p>
          ) : articles.length === 0 ? (
            <p>記事がありません。新しい記事を作成してください。</p>
          ) : (
            <div className="articles-list">
              {articles.map((article) => {
                const isExpanded = expandedArticles[article.id];
                const isPosting = postingArticles[article.id];
                const cleanedTitle = cleanTitle(article.title);
                const cleanedContent = cleanContent(article.content);
                
                return (
                  <div key={article.id} className={`article-item ${article.posted ? 'article-posted' : ''}`}>
                    <div className="article-header">
                      <h3>{cleanedTitle}</h3>
                      {article.posted && (
                        <span className="posted-badge">✓ 投稿完了</span>
                      )}
                    </div>
                    <p className="article-meta">
                      {article.theme && <span className="badge">テーマ: {article.theme}</span>}
                      {article.trend_keyword && (
                        <span className="badge">トレンド: {article.trend_keyword}</span>
                      )}
                      {article.posted_at && (
                        <span className="badge badge-posted">投稿日時: {article.posted_at}</span>
                      )}
                    </p>
                    <div className="article-content">
                      {isExpanded ? (
                        <div className="article-full">
                          <pre className="article-text">{cleanedContent}</pre>
                        </div>
                      ) : (
                        <p className="article-preview">
                          {cleanedContent.substring(0, 200)}...
                        </p>
                      )}
                    </div>
                    <div className="article-actions">
                      <button
                        onClick={() => toggleExpand(article.id)}
                        className="btn btn-secondary"
                      >
                        {isExpanded ? '本文を折りたたむ' : '全文表示'}
                      </button>
                      {!article.posted && (
                        <button
                          onClick={() => handlePost(article.id)}
                          className="btn btn-primary"
                          disabled={isPosting}
                        >
                          {isPosting ? '投稿中...' : '投稿'}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(article.id)}
                        className="btn btn-danger"
                      >
                        削除
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

