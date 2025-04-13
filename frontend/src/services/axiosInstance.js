import axios from 'axios';
import AuthService from './authService';
import { useAuth } from '../context/AuthContext.jsx';

const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login'; 
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: `/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.request.use(config => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

axiosInstance.interceptors.response.use(
  response => {
    return response;
  },
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && originalRequest.url !== '/authorizer/token/refresh/') {
        
        if (isRefreshing) {
            return new Promise(function(resolve, reject) {
                failedQueue.push({resolve, reject})
            }).then(token => {
                originalRequest.headers['Authorization'] = 'Bearer ' + token;
                return axiosInstance(originalRequest);
            }).catch(err => {
                return Promise.reject(err);
            })
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
             console.error("No refresh token available.");
             isRefreshing = false;
             handleLogout();
             return Promise.reject(error);
        }

        try {
            const refreshResponse = await AuthService.refreshToken(refreshToken);
            const newAccessToken = refreshResponse.access;
            
            localStorage.setItem('accessToken', newAccessToken);
            axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
            originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
            
            processQueue(null, newAccessToken);
            
            return axiosInstance(originalRequest);
        } catch (refreshError) {
            console.error("Unable to refresh token", refreshError);
            processQueue(refreshError, null);
            handleLogout();
            return Promise.reject(refreshError);
        } finally {
             isRefreshing = false;
        }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance; 