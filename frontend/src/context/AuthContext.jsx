import React, { createContext, useState, useContext, useEffect } from 'react';
import axiosInstance from '../services/axiosInstance'; // Import axiosInstance để set header

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('accessToken'));
  const [currentUserInfo, setCurrentUserInfo] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    setAuthLoading(true);
    try {
      const storedToken = localStorage.getItem('accessToken');
      const storedUserInfo = localStorage.getItem('userInfo');
      
      if (storedToken && storedUserInfo) {
        setToken(storedToken);
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        try {
          const parsedUser = JSON.parse(storedUserInfo);
          setCurrentUserInfo(parsedUser);
          setIsAuthenticated(true);
        } catch (parseError) {
          console.error('[AuthContext] Error parsing stored userInfo:', parseError);
          // Nếu userInfo lỗi, coi như chưa đăng nhập
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userInfo');
          setToken(null);
          setCurrentUserInfo(null);
          setIsAuthenticated(false);
          delete axiosInstance.defaults.headers.common['Authorization'];
        }
      } else {
        // Nếu một trong hai thiếu, logout
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userInfo');
        setToken(null);
        setCurrentUserInfo(null);
        setIsAuthenticated(false);
        delete axiosInstance.defaults.headers.common['Authorization'];
      }
    } catch (error) {
        console.error("[AuthContext] Error during initial auth check:", error);
        setToken(null);
        setCurrentUserInfo(null);
        setIsAuthenticated(false);
        delete axiosInstance.defaults.headers.common['Authorization'];
    } finally {
        setAuthLoading(false);
    }
  }, []);

  const login = async (accessToken, refreshToken, userInfo) => { // Thêm userInfo
    setAuthLoading(true);
    try {
      if (!userInfo || !userInfo.id) {
        console.error('[AuthContext] Login attempt with invalid userInfo:', userInfo);
        throw new Error('User information is missing or invalid during login.');
      }
      localStorage.setItem('accessToken', accessToken);
      if (refreshToken) {
          localStorage.setItem('refreshToken', refreshToken);
      }
      localStorage.setItem('userInfo', JSON.stringify(userInfo)); // LƯU userInfo
      
      setCurrentUserInfo(userInfo); // Set state mới
      setToken(accessToken);
      setIsAuthenticated(true);
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      setAuthLoading(false);
      return true;
    } catch (error) {
        console.error("[AuthContext] Login processing error:", error);
        // Gọi hàm logout nội bộ để dọn dẹp, không dùng logout toàn cục để tránh redirect ngay
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userInfo');
        setCurrentUserInfo(null);
        setToken(null);
        setIsAuthenticated(false);
        delete axiosInstance.defaults.headers.common['Authorization'];
        setAuthLoading(false);
        return false;
    }
  };

  const logout = async () => {
    try {
      setIsAuthenticated(false);
      setToken(null);
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userInfo');
      localStorage.removeItem('isAuthenticated');

      setCurrentUserInfo(null); // Xóa state userInfo
      setIsAuthenticated(false);
      setToken(null);
      delete axiosInstance.defaults.headers.common['Authorization'];
      
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const value = {
    token,
    currentUserInfo,
    isAuthenticated,
    authLoading,
    login,
    logout,
    user: currentUserInfo,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
}; 