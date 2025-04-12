import axios from 'axios';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';

export const getArticles = async (page = 1, limit = 10) => {
  try {
    const response = await axios.get(`${API_URL}/news/articles/`, {
      headers: {
        'Accept': 'application/json',
      }
    });
    return {
      results: response.data.results,
      count: response.data.count,
      next: response.data.next,
      previous: response.data.previous
    };
  } catch (error) {
    console.error('Error fetching articles:', error);
    throw error;
  }
};

export const getTrendingArticles = async (limit = 10) => {
  try {
    const response = await axios.get(`${API_URL}/news/articles/trending/`, {
      params: { 
        page_size: limit 
      },
      headers: {
        'Accept': 'application/json',
      }
    });
    return {
      results: response.data.results,
      count: response.data.count
    };
  } catch (error) {
    console.error('Error fetching trending articles:', error);
    throw error;
  }
};

export const saveArticle = async (articleId) => {
  try {
    const response = await axios.post(`${API_URL}/news/articles/${articleId}/save/`, null, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error saving article:', error);
    throw error;
  }
}; 