import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Trending from './pages/Trending';
import FavouriteCategories from './pages/FavouriteCategories';
import Bookmark from './pages/Bookmark';
import Profile from './pages/Profile';
import Theme from './pages/Theme';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
// import NotFoundPage from './pages/NotFoundPage';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import ProtectedRoute from './components/ProtectedRoute';
import "./App.css";

const { Content } = Layout;

const AppContent = () => {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarExpandedWidth = 250;
  const sidebarCollapsedWidth = 80;
  const mainContentMarginLeft = collapsed ? sidebarCollapsedWidth : sidebarExpandedWidth;
  const { isAuthenticated } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isAuthenticated && <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />}
      <Layout style={{ marginLeft: isAuthenticated ? mainContentMarginLeft : 0, transition: 'margin-left 0.2s' }}>
        <Content style={{ margin: '1vh', overflow: 'auto' }}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trending"
              element={
                <ProtectedRoute>
                  <Trending />
                </ProtectedRoute>
              }
            />
            <Route
              path="/favourite-categories"
              element={
                <ProtectedRoute>
                  <FavouriteCategories />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bookmark"
              element={
                <ProtectedRoute>
                  <Bookmark />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/theme"
              element={
                <ProtectedRoute>
                  <Theme />
                </ProtectedRoute>
              }
            />

            {isAuthenticated && <Route path="*" element={<Navigate to="/" replace />} />}
            {!isAuthenticated && <Route path="*" element={<Navigate to="/login" replace />} />}
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
