import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// セッションID管理
const getSessionId = () => {
  return localStorage.getItem('session_id');
};

const setSessionId = (sessionId) => {
  if (sessionId) {
    localStorage.setItem('session_id', sessionId);
    api.defaults.headers.common['X-Session-ID'] = sessionId;
  }
};

// リクエストインターセプター: すべてのリクエストにセッションIDを追加
api.interceptors.request.use(
  (config) => {
    const sessionId = getSessionId();
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId;
      console.log('リクエストにセッションIDを追加:', sessionId.substring(0, 8) + '...');
    } else {
      console.warn('セッションIDがありません');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター: 401エラーの処理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('認証エラー:', error.response.data);
      // セッション切れの場合はログアウト
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('session_id');
        alert('セッションが切れました。再ログインしてください。');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// 認証
export const login = async (password) => {
  const response = await api.post('/api/auth/login', { password });
  if (response.data.success && response.data.session_id) {
    console.log('ログイン成功、セッションID:', response.data.session_id.substring(0, 8) + '...');
    setSessionId(response.data.session_id);
  } else {
    console.error('セッションIDが返されませんでした:', response.data);
  }
  return response.data;
};

// 設定（セッションIDは自動で追加される）
export const getSettings = async () => {
  const response = await api.get('/api/settings');
  return response.data;
};

export const updateSettings = async (settings) => {
  const response = await api.post('/api/settings', settings);
  return response.data;
};

// プロンプト設定
export const getPromptSettings = async () => {
  const response = await api.get('/api/prompt-settings');
  return response.data;
};

export const updatePromptSettings = async (settings) => {
  const response = await api.post('/api/prompt-settings', settings);
  return response.data;
};

// テーマ
export const getThemes = async () => {
  const response = await api.get('/api/themes');
  return response.data;
};

// 記事生成
export const generateThemeArticle = async (theme, llmProvider) => {
  const response = await api.post('/api/articles/generate/theme', null, {
    params: { theme, llm_provider: llmProvider },
  });
  return response.data;
};

export const generateTrendArticle = async (theme, trendKeyword, llmProvider) => {
  const response = await api.post('/api/articles/generate/trend', null, {
    params: { theme, trend_keyword: trendKeyword, llm_provider: llmProvider },
  });
  return response.data;
};

export const generateManualArticle = async (article) => {
  const response = await api.post('/api/articles/generate/manual', article);
  return response.data;
};

// 記事
export const getArticles = async () => {
  const response = await api.get('/api/articles');
  return response.data;
};

export const getArticle = async (articleId) => {
  const response = await api.get(`/api/articles/${articleId}`);
  return response.data;
};

// 下書き投稿
export const postDraft = async (articleId, scheduledTime = null) => {
  const params = scheduledTime ? { scheduled_time: scheduledTime } : {};
  const response = await api.post(`/api/articles/${articleId}/post`, null, { params });
  return response.data;
};

// X投稿用本文生成
export const generateXPost = async (articleId, llmProvider = 'openai') => {
  const response = await api.post(`/api/articles/${articleId}/x-post`, null, {
    params: { llm_provider: llmProvider },
  });
  return response.data;
};

// トレンド取得
export const getTrends = async (limit = 10) => {
  const response = await api.get('/api/trends', { params: { limit } });
  return response.data;
};

// 記事削除
export const deleteArticle = async (articleId) => {
  const response = await api.delete(`/api/articles/${articleId}`);
  return response.data;
};

// スケジュール管理
export const getSchedules = async () => {
  const response = await api.get('/api/schedules');
  return response.data;
};

export const addSchedule = async (scheduleData) => {
  const response = await api.post('/api/schedules', scheduleData);
  return response.data;
};

export const deleteSchedule = async (scheduleId) => {
  const response = await api.delete(`/api/schedules/${scheduleId}`);
  return response.data;
};

