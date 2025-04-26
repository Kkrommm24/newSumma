import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance from '../../services/axiosInstance';

export const fetchFavoriteKeywords = createAsyncThunk(
  'user/fetchFavoriteKeywords',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/user/fav-words');
      return response.data.favorite_keywords || [];
    } catch (error) {
      console.error("Error fetching keywords:", error.response || error);
      return rejectWithValue(error.response?.data || 'Failed to fetch keywords');
    }
  }
);

export const addFavoriteKeyword = createAsyncThunk(
  'user/addFavoriteKeyword',
  async (keyword, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.patch('/user/fav-words', { keywords: [keyword] });
      return response.data.favorite_keywords || [];
    } catch (error) {
      console.error("Error adding keyword:", error.response || error);
      return rejectWithValue({ errorData: error.response?.data, keyword });
    }
  }
);

export const deleteFavoriteKeyword = createAsyncThunk(
  'user/deleteFavoriteKeyword',
  async (keyword, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.delete('/user/fav-words', { data: { keywords: [keyword] } });
      return response.data.favorite_keywords || [];
    } catch (error) {
      console.error("Error deleting keyword:", error.response || error);
      return rejectWithValue({ errorData: error.response?.data, keyword });
    }
  }
);

export const fetchSearchHistory = createAsyncThunk(
  'user/fetchSearchHistory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/user/search-history');
      return response.data || [];
    } catch (error) {
      console.error("Error fetching search history:", error.response || error);
      return rejectWithValue(error.response?.data || 'Failed to fetch search history');
    }
  }
);

export const addSearchHistory = createAsyncThunk(
  'user/addSearchHistory',
  async (query, { dispatch, rejectWithValue }) => {
    try {
      await axiosInstance.post('/user/search-history', { query: query.trim() });
      dispatch(fetchSearchHistory()); 
      return query;
    } catch (error) { 
      console.error("Error adding search history:", error.response || error);
      return rejectWithValue({ errorData: error.response?.data, query });
    }
  }
);

export const deleteSearchHistoryItem = createAsyncThunk(
  'user/deleteSearchHistoryItem',
  async (queryToDelete, { dispatch, rejectWithValue }) => {
    try {
      await axiosInstance.delete('/user/search-history', { data: { queries: [queryToDelete] } });
      dispatch(fetchSearchHistory());
      return queryToDelete;
    } catch (error) {
      console.error("Error deleting search history item:", error.response || error);
       return rejectWithValue({ errorData: error.response?.data, query: queryToDelete });
    }
  }
);

export const fetchBookmarks = createAsyncThunk(
  'user/fetchBookmarks',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/user/bookmarks');
      return response.data || []; 
    } catch (error) {
      console.error("Error fetching bookmarks:", error.response || error);
      return rejectWithValue(error.response?.data || 'Failed to fetch bookmarks');
    }
  }
);

export const removeBookmark = createAsyncThunk(
  'user/removeBookmark',
  async (articleId, { dispatch, rejectWithValue }) => {
    try {
      await axiosInstance.delete('/user/bookmarks', { data: { article_ids: [articleId] } });
      dispatch(fetchBookmarks());
      return articleId;
    } catch (error) {
      console.error("Error removing bookmark:", error.response || error);
       return rejectWithValue({ errorData: error.response?.data, articleId });
    }
  }
);

export const addBookmark = createAsyncThunk(
  'user/addBookmark',
  async (articleId, { dispatch, rejectWithValue }) => {
    try {
      await axiosInstance.post('/user/bookmarks', { article_id: articleId });
      dispatch(fetchBookmarks()); 
      return articleId;
    } catch (error) {
      console.error("Error adding bookmark:", error.response || error);
       return rejectWithValue({ errorData: error.response?.data, articleId });
    }
  }
);


const initialState = {
  favoriteKeywords: {
    items: [],
    status: 'idle', // idle | loading | succeeded | failed
    error: null,
  },
  searchHistory: {
    items: [],
    status: 'idle', // idle | loading | succeeded | failed
    error: null,
  },
  bookmarks: {
    items: [], 
    status: 'idle', // idle | loading | succeeded | failed
    error: null,
  }
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    resetUserState: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      // Fetch Keywords
      .addCase(fetchFavoriteKeywords.pending, (state) => {
        state.favoriteKeywords.status = 'loading';
      })
      .addCase(fetchFavoriteKeywords.fulfilled, (state, action) => {
        state.favoriteKeywords.status = 'succeeded';
        state.favoriteKeywords.items = action.payload;
        state.favoriteKeywords.error = null;
      })
      .addCase(fetchFavoriteKeywords.rejected, (state, action) => {
        state.favoriteKeywords.status = 'failed';
        state.favoriteKeywords.error = action.payload || action.error.message;
      })
      // Add Keyword
      .addCase(addFavoriteKeyword.pending, (state) => {
        // Có thể set state loading riêng cho việc thêm nếu cần
      })
      .addCase(addFavoriteKeyword.fulfilled, (state, action) => {
        state.favoriteKeywords.items = action.payload; 
        state.favoriteKeywords.error = null;
      })
      .addCase(addFavoriteKeyword.rejected, (state, action) => {
         console.error("Add keyword rejected payload:", action.payload);
         state.favoriteKeywords.error = `Không thể thêm từ khóa "${action.payload?.keyword}".`; 
      })
       .addCase(deleteFavoriteKeyword.pending, (state) => {
        // Có thể set state loading riêng cho việc xóa nếu cần
      })
      .addCase(deleteFavoriteKeyword.fulfilled, (state, action) => {
        state.favoriteKeywords.items = action.payload; 
        state.favoriteKeywords.error = null;
      })
      .addCase(deleteFavoriteKeyword.rejected, (state, action) => {
         // Xử lý lỗi khi xóa
         console.error("Delete keyword rejected payload:", action.payload);
         state.favoriteKeywords.error = `Không thể xóa từ khóa "${action.payload?.keyword}".`;
      })
      
      // Search History Reducers
      .addCase(fetchSearchHistory.pending, (state) => {
        state.searchHistory.status = 'loading';
      })
      .addCase(fetchSearchHistory.fulfilled, (state, action) => {
        state.searchHistory.status = 'succeeded';
        state.searchHistory.items = action.payload;
        state.searchHistory.error = null;
      })
      .addCase(fetchSearchHistory.rejected, (state, action) => {
        state.searchHistory.status = 'failed';
        state.searchHistory.error = action.payload || action.error.message;
      })
       .addCase(addSearchHistory.rejected, (state, action) => {
           console.error("Add search history rejected:", action.payload);
           state.searchHistory.error = `Không thể lưu tìm kiếm "${action.meta.arg}".`;
       })
       .addCase(deleteSearchHistoryItem.rejected, (state, action) => {
           console.error("Delete search history rejected:", action.payload);
           state.searchHistory.error = `Không thể xóa tìm kiếm "${action.meta.arg}".`;
       })

      .addCase(fetchBookmarks.pending, (state) => {
        state.bookmarks.status = 'loading';
      })
      .addCase(fetchBookmarks.fulfilled, (state, action) => {
        state.bookmarks.status = 'succeeded';
        state.bookmarks.items = action.payload;
        state.bookmarks.error = null;
      })
      .addCase(fetchBookmarks.rejected, (state, action) => {
        state.bookmarks.status = 'failed';
        state.bookmarks.error = action.payload || action.error.message;
      })

       .addCase(addBookmark.rejected, (state, action) => {
           console.error("Add bookmark rejected:", action.payload);
           state.bookmarks.error = `Không thể lưu bài viết (ID: ${action.meta.arg}).`;
       })
       .addCase(removeBookmark.rejected, (state, action) => {
           console.error("Remove bookmark rejected:", action.payload);
           state.bookmarks.error = `Không thể xóa bài viết đã lưu (ID: ${action.meta.arg}).`;
       });
  },
});

export const { resetUserState } = userSlice.actions;

export default userSlice.reducer; 