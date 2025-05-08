import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../services/axiosInstance';

const NEWS_PER_PAGE = 10;

const getRequestKey = (mode, query) => {
  return query ? `search:${query}` : mode;
};

export const fetchNews = createAsyncThunk(
  'news/fetchNews',
  async ({ mode, query, page }, { rejectWithValue }) => {
    let url = '';
    let params = {};

    try {
      if (query) {
        url = `/summarizer/summaries/search/`;
        params = { q: query, page: page, page_size: NEWS_PER_PAGE };
      } else if (mode === 'trending') {
        url = `/summarizer/summaries/`;
        params = { sort_by: '-created_at', page: page, page_size: NEWS_PER_PAGE };
      } else {
        const currentOffset = (page - 1) * NEWS_PER_PAGE;
        url = `/recommender/recommendations/`;
        params = { limit: NEWS_PER_PAGE, offset: currentOffset };
      }
      
      const response = await axiosInstance.get(url, { params });
      const data = response.data;

      if (data && data.results) {
        const formattedData = data.results.map(item => ({
            id: item.id,
            articleId: item.article_id,
            title: item.title || 'Không có tiêu đề',
            summary: item.summary_text || item.summary || 'Không có tóm tắt',
            imageUrl: item.image_url || null,
            sourceUrl: item.url || '#',
            keywords: item.keywords || [],
            publishedAt: item.published_at || null,
            userVote: item.user_vote === true ? true : item.user_vote === false ? false : null,
            upvotes: item.upvotes,
            downvotes: item.downvotes,
            comment_count: item.comment_count === undefined ? 0 : item.comment_count
        }));
        
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

const initialState = {
  requests: {},
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
            requestState.currentPage = page + 1;
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
      });
  },
});

export const { resetNewsState, resetAllNews } = newsSlice.actions;

export default newsSlice.reducer; 