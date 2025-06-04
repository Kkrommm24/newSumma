import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../services/axiosInstance';

const NEWS_PER_PAGE = 10;

const getRequestKey = (mode, query) => {
  return query ? `search:${query}` : mode;
};

export const fetchNews = createAsyncThunk(
  'news/fetchNews',
  async ({ mode, query, page }, { rejectWithValue, getState }) => {
    let url = '';
    let params = {};
    const state = getState();
    const requestKey = getRequestKey(mode, query);
    const currentState = state.news.requests[requestKey];

    try {
      if (query) {
        url = `/summarizer/summaries/search/`;
        params = { q: query, page: page, page_size: NEWS_PER_PAGE };
      } else if (mode === 'trending') {
        url = `/summarizer/summaries/`;
        params = { sort_by: '-created_at', page: page, page_size: NEWS_PER_PAGE };
      } else {
        const currentOffset = currentState ? currentState.items.length : 0;
        url = `/recommender/recommendations/`;
        params = { limit: NEWS_PER_PAGE, offset: currentOffset };
      }
      
      const response = await axiosInstance.get(url, { params });
      const data = response.data;

      if (data && data.summaries) {
        const formattedData = data.summaries.map(item => {
          if (!item.article || !item.article.id) { 
            console.warn(`[fetchNews - data.summaries] Summary ID ${item.id} has missing or incomplete 'article' object. API Response:`, item);
            return {
              id: item.id,
              articleId: null, 
              title: item.article?.title || 'Không có tiêu đề',
              summary: item.summary_text || 'Không có tóm tắt',
              imageUrl: item.article?.image_url || null,
              sourceUrl: item.article?.url || '#',
              keywords: item.article?.keywords || [],
              publishedAt: item.article?.published_at || null,
              userVote: item.user_vote,
              upvotes: item.upvotes || 0,
              downvotes: item.downvotes || 0,
              comment_count: item.comment_count === undefined ? 0 : item.comment_count,
              category_name: item.category_name || null
            };
          }
          return {
            id: item.id,
            articleId: item.article.id,
            title: item.article.title || 'Không có tiêu đề',
            summary: item.summary_text || 'Không có tóm tắt',
            imageUrl: item.article.image_url || null,
            sourceUrl: item.article.url || '#',
            keywords: item.article.keywords || [],
            publishedAt: item.article.published_at || null,
            userVote: item.user_vote,
            upvotes: item.upvotes || 0,
            downvotes: item.downvotes || 0,
            comment_count: item.comment_count === undefined ? 0 : item.comment_count,
            category_name: item.category_name || null
          };
        });
        
        return { 
          items: formattedData, 
          totalCount: data.source?.total_count || formattedData.length,
          hasMore: data.source?.has_more || false,
          page: page, 
          mode: mode, 
          query: query 
        };
      } else if (data && data.results) {
        const formattedData = data.results.map(item => {
            if (!item.article || !item.article.id) {
                console.warn(`[fetchNews - data.results] Summary ID ${item.id} has missing or incomplete 'article' object. API Response:`, item);
                return {
                    id: item.id,
                    articleId: null,
                    title: item.article?.title || 'Không có tiêu đề',
                    summary: item.summary_text || item.summary || 'Không có tóm tắt',
                    imageUrl: item.article?.image_url || null,
                    sourceUrl: item.article?.url || '#',
                    keywords: item.article?.keywords || [],
                    publishedAt: item.article?.published_at || null,
                    userVote: item.user_vote,
                    upvotes: item.upvotes || 0,
                    downvotes: item.downvotes || 0,
                    comment_count: item.comment_count === undefined ? 0 : item.comment_count,
                    category_name: item.category_name || null
                };
            }
            return {
                id: item.id,
                articleId: item.article.id,
                title: item.article.title || 'Không có tiêu đề',
                summary: item.summary_text || item.summary || 'Không có tóm tắt',
                imageUrl: item.article.image_url || null,
                sourceUrl: item.article.url || '#',
                keywords: item.article.keywords || [],
                publishedAt: item.article.published_at || null,
                userVote: item.user_vote,
                upvotes: item.upvotes || 0,
                downvotes: item.downvotes || 0,
                comment_count: item.comment_count === undefined ? 0 : item.comment_count,
                category_name: item.category_name || null
            };
        });
        
        const totalCount = data.count || 0;
        const receivedItemsCount = data.results.length;
        
        const totalPages = Math.ceil(totalCount / NEWS_PER_PAGE);
        const calculatedHasMore = page < totalPages;

        return { 
            items: formattedData, 
            totalCount: totalCount,
            hasMore: calculatedHasMore,
            page: page, 
            mode: mode, 
            query: query 
        };
      } else {
        console.warn(`[fetchNews fulfilled] Page: ${page}, Query: ${query} - API response missing results:`, data);
        return { items: [], totalCount: 0, hasMore: false, page: page, mode: mode, query: query };
      }
    } catch (error) {
      console.error(`[fetchNews rejected] Page: ${page}, Query: ${query}`, error.response || error);
      return rejectWithValue(error.response?.data || 'Failed to fetch news');
    }
  }
);

export const submitFeedback = createAsyncThunk(
  'news/submitFeedback',
  async ({ summaryId, isUpvote }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/summarizer/summaries/feedback/', {
        summary_id: summaryId,
        is_upvote: isUpvote
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Failed to submit feedback');
    }
  }
);

const initialState = {
  requests: {},
  userVotes: JSON.parse(localStorage.getItem('userVotes')) || {},
};

const newsSlice = createSlice({
  name: 'news',
  initialState,
  reducers: {
    resetNewsState: (state, action) => {
        const { mode, query } = action.payload;
        const requestKey = getRequestKey(mode, query);
        delete state.requests[requestKey];
    },
    resetAllNews: (state) => {
        state.requests = {};
    },
    syncUserVotes: (state, action) => {
        state.userVotes = action.payload;
        localStorage.setItem('userVotes', JSON.stringify(action.payload));
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNews.pending, (state, action) => {
        const { mode, query } = action.meta.arg;
        const requestKey = getRequestKey(mode, query);
        if (!state.requests[requestKey]) {
          state.requests[requestKey] = { items: [], status: 'idle', error: null, currentPage: 1, totalCount: 0, hasMore: true };
        }
        state.requests[requestKey].status = 'loading';
      })
      .addCase(fetchNews.fulfilled, (state, action) => {
        const { items, totalCount, hasMore, page, mode, query } = action.payload;
        const requestKey = getRequestKey(mode, query);
        
        const requestState = state.requests[requestKey];
        
        if(requestState) {
            requestState.status = 'succeeded';
            if (page === 1) {
                requestState.items = items; 
            } else {
                const existingIds = new Set(requestState.items.map(item => item.id));
                const newItems = items.filter(item => !existingIds.has(item.id));
                requestState.items = [...requestState.items, ...newItems];
            }
            requestState.totalCount = totalCount;
            requestState.hasMore = hasMore;
            requestState.currentPage = page;
            requestState.error = null;
        }
      })
      .addCase(fetchNews.rejected, (state, action) => {
        const { mode, query, page } = action.meta.arg;
        const requestKey = getRequestKey(mode, query);
        if (state.requests[requestKey]) {
          state.requests[requestKey].status = 'failed';
          state.requests[requestKey].error = action.payload || action.error.message || 'Unknown error';
          if (action.error.message?.includes("404") || action.payload?.includes("Invalid page")) {
              state.requests[requestKey].hasMore = false; 
          }
        }
      })
      .addCase(submitFeedback.fulfilled, (state, action) => {
        const { summary_id, upvotes, downvotes, user_vote } = action.payload;
        
        if (user_vote === null) {
          delete state.userVotes[summary_id];
        } else {
          state.userVotes[summary_id] = user_vote;
        }
        
        localStorage.setItem('userVotes', JSON.stringify(state.userVotes));
        
        Object.values(state.requests).forEach(requestState => {
          const item = requestState.items.find(item => item.id === summary_id);
          if (item) {
            item.upvotes = upvotes;
            item.downvotes = downvotes;
            item.userVote = user_vote;
          }
        });
      })
      .addCase(submitFeedback.rejected, (state, action) => {
        console.error('Feedback submission failed:', action.payload);
      });
  },
});

export const { resetNewsState, resetAllNews, syncUserVotes } = newsSlice.actions;

export default newsSlice.reducer; 