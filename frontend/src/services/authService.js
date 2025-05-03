import axiosInstance from './axiosInstance';

const AuthService = {
  login: async (username, password) => {
    try {
      const response = await axiosInstance.post('/authorizer/token/', {
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
      const response = await axiosInstance.post('/user/register', {
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
      return response.data;
    } catch (error) {
      console.error('Refresh token API error:', error.response || error);
      throw error;
    }
  },

};

export default AuthService; 