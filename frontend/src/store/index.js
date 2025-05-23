import { configureStore } from '@reduxjs/toolkit';
import newsReducer from './slices/newsSlice'; 
import userReducer from './slices/userSlice';
import adminReducer from './slices/adminSlice';

export const store = configureStore({
  reducer: {
    news: newsReducer,
    user: userReducer,
    admin: adminReducer
  },
}); 