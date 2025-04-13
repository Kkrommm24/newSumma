import React, { createContext, useState, useContext, useEffect } from 'react';
import axiosInstance from '../services/axiosInstance'; // Import axiosInstance để set header

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('accessToken'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('accessToken'));
  const [authLoading, setAuthLoading] = useState(true);
  // const [user, setUser] = useState(null); // Có thể thêm state user nếu cần lưu thông tin người dùng

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('accessToken');
      if (storedToken) {
        setToken(storedToken);
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        setIsAuthenticated(true);
      } else {
        setToken(null);
        setIsAuthenticated(false);
        delete axiosInstance.defaults.headers.common['Authorization'];
      }
    } catch (error) {
        console.error("Error during initial auth check:", error);
        setToken(null);
        setIsAuthenticated(false);
        delete axiosInstance.defaults.headers.common['Authorization'];
    } finally {
        setAuthLoading(false);
    }
  }, []);

  const login = async (accessToken, refreshToken) => {
    setAuthLoading(true);
    try {
      localStorage.setItem('accessToken', accessToken);
      if (refreshToken) {
          localStorage.setItem('refreshToken', refreshToken);
      }
      setToken(accessToken);
      setIsAuthenticated(true);
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      setAuthLoading(false);
      return true;
    } catch (error) {
        console.error("Login processing error:", error);
        logout();
        setAuthLoading(false);
        return false;
    }
  };

  const logout = () => {
    setAuthLoading(true);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setToken(null);
    setIsAuthenticated(false);
    // setUser(null);
    // Xóa header Authorization
    delete axiosInstance.defaults.headers.common['Authorization'];
    setAuthLoading(false);
  };

  const value = {
    token,
    isAuthenticated,
    authLoading,
    login,
    logout,
    // user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
}; 