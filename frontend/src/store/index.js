import { configureStore } from '@reduxjs/toolkit';
// Import các reducer từ slice sau này
import newsReducer from './slices/newsSlice'; 
import userReducer from './slices/userSlice'; // Import userReducer

export const store = configureStore({
  reducer: {
    news: newsReducer, // Thêm newsReducer
    user: userReducer, // Thêm userReducer
    // Thêm các reducer khác nếu có
  },
  // Middleware mặc định của Redux Toolkit đã bao gồm redux-thunk
  // và các middleware hữu ích khác
}); 