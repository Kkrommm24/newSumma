import axiosInstance from './axiosInstance';

const API_URL = '/authorizer/';
const USER_API_URL = '/user/';

const AuthService = {
  login: async (username, password) => {
    try {
      const response = await axiosInstance.post(`${API_URL}token/`, {
        username,
        password,
      });
      return response.data;
    } catch (error) {
      console.error('Login API error:', error.response || error);
      throw error;
    }
  },

  register: async (username, email, password, password2) => {
    try {
      const response = await axiosInstance.post(`${USER_API_URL}register`, {
        username,
        email,
        password,
        password2,
      });
      return response.data;
    } catch (error) {
      console.error('Registration API error:', error.response || error);
      throw error; 
    }
  },

  // Thêm hàm refresh token
  refreshToken: async (refresh) => {
    try {
      const response = await axiosInstance.post('/authorizer/token/refresh/', {
        refresh: refresh
      });
      return response.data; // Trả về { access: "new_access_token" }
    } catch (error) {
      console.error('Refresh token API error:', error.response || error);
      throw error; // Ném lỗi để interceptor xử lý logout
    }
  },

  // Có thể thêm các hàm khác như register, refreshToken ở đây
};

export default AuthService; 