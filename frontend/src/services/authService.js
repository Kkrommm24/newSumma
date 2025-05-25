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
      const response = await axiosInstance.post('/user/register/', {
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

  getUserProfile: async () => {
    try {
        const response = await axiosInstance.get('/user/profile/');
        return response.data;
    } catch (error) {
        console.error('Get User Profile API error:', error.response || error);
        throw error;
    }
  },

  updateUserProfile: async (formData) => {
      try {
          const response = await axiosInstance.put('/user/profile/', formData, {
              headers: {
                  'Content-Type': undefined, 
              }
          });
          return response.data;
      } catch (error) {
          console.error('Update User Profile API error:', error.response || error);
          throw error;
      }
  },

  changePassword: async (data) => {
      try {
          const response = await axiosInstance.post('/user/change-password/', data);
          return response.data;
      } catch (error) {
          console.error('Change Password API error:', error.response || error);
          throw error;
      }
  },

  deleteAccount: async (password) => {
      try {
          const response = await axiosInstance.post('/user/delete-account/', { password });
          return response.data;
      } catch (error) {
          console.error('Delete Account API error:', error.response || error);
          throw error;
      }
  },

};

export default AuthService; 