import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  stats: null,
  users: [],
  articles: [],
  summaries: [],
  comments: [],
  favoriteWords: [],
  keywordUsers: [],
  loading: false,
  pagination: {
    current: 1,
    pageSize: 10,
    total: 0
  },
  keywordUsersPagination: {
    current: 1,
    pageSize: 10,
    total: 0
  },
  selectedKeyword: null
};

const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    setStats: (state, action) => {
      state.stats = action.payload;
    },
    setUsers: (state, action) => {
      state.users = action.payload;
    },
    setArticles: (state, action) => {
      state.articles = action.payload;
    },
    setSummaries: (state, action) => {
      state.summaries = action.payload;
    },
    setComments: (state, action) => {
      state.comments = action.payload;
    },
    setFavoriteWords: (state, action) => {
      state.favoriteWords = action.payload;
    },
    setKeywordUsers: (state, action) => {
      state.keywordUsers = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setPagination: (state, action) => {
      state.pagination = action.payload;
    },
    setKeywordUsersPagination: (state, action) => {
      state.keywordUsersPagination = action.payload;
    },
    setSelectedKeyword: (state, action) => {
      state.selectedKeyword = action.payload;
    },
    resetAdminState: (state) => {
      return initialState;
    }
  }
});

export const {
  setStats,
  setUsers,
  setArticles,
  setSummaries,
  setComments,
  setFavoriteWords,
  setKeywordUsers,
  setLoading,
  setPagination,
  setKeywordUsersPagination,
  setSelectedKeyword,
  resetAdminState
} = adminSlice.actions;

export default adminSlice.reducer; 