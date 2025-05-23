import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout, App as AntApp, ConfigProvider } from 'antd';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Trending from './pages/Trending';
import FavouriteCategories from './pages/FavouriteCategories';
import Bookmark from './pages/Bookmark';
import Profile from './pages/Profile';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AdminDashboard from './pages/AdminDashboard';
// import NotFoundPage from './pages/NotFoundPage';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import ProtectedRoute from './components/ProtectedRoute';
import { colors } from './theme/colors';
import "./App.css";
import ScrollToTop from './components/ScrollToTop';

const { Content } = Layout;

const AppContent = () => {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarExpandedWidth = 250;
  const sidebarCollapsedWidth = 80;
  const mainContentMarginLeft = collapsed ? sidebarCollapsedWidth : sidebarExpandedWidth;
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  const showSidebar = isAuthenticated && location.pathname !== '/admin';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {showSidebar && <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />}
      <Layout style={{ marginLeft: showSidebar ? mainContentMarginLeft : 0, transition: 'margin-left 0.2s' }}>
        <Content style={{ margin: '1vh', overflow: 'auto' }}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password/:reset_token" element={<ResetPasswordPage />} />

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
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            {isAuthenticated && <Route path="*" element={<Navigate to="/" replace />} />}
            {!isAuthenticated && <Route path="*" element={<Navigate to="/login" replace />} />}
          </Routes>
        </Content>
      </Layout>
      <ScrollToTop />
    </Layout>
  );
};

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: colors.primary.main,
          colorPrimaryHover: colors.primary.light,
          colorPrimaryActive: colors.primary.dark,
          colorPrimaryBg: colors.background.dark,
          colorPrimaryBgHover: colors.action.hover,
          colorPrimaryBorder: 'transparent',
          colorPrimaryBorderHover: 'transparent',

          colorSuccess: colors.success.main,
          colorSuccessHover: colors.success.light,
          colorSuccessActive: colors.success.dark,
          colorSuccessBg: colors.success.light,
          colorSuccessBgHover: colors.success.main,
          colorSuccessBorder: 'transparent',
          colorSuccessBorderHover: 'transparent',

          colorWarning: colors.warning.main,
          colorWarningHover: colors.warning.light,
          colorWarningActive: colors.warning.dark,
          colorWarningBg: colors.warning.light,
          colorWarningBgHover: colors.warning.main,
          colorWarningBorder: 'transparent',
          colorWarningBorderHover: 'transparent',

          colorError: colors.error.main,
          colorErrorHover: colors.error.light,
          colorErrorActive: colors.error.dark,
          colorErrorBg: colors.error.light,
          colorErrorBgHover: colors.error.main,
          colorErrorBorder: 'transparent',
          colorErrorBorderHover: 'transparent',

          colorInfo: colors.info.main,
          colorInfoHover: colors.info.light,
          colorInfoActive: colors.info.dark,
          colorInfoBg: colors.info.light,
          colorInfoBgHover: colors.info.main,
          colorInfoBorder: 'transparent',
          colorInfoBorderHover: 'transparent',

          colorTextBase: colors.text.primary,
          colorTextSecondary: colors.text.secondary,
          colorTextDisabled: colors.text.disabled,
          colorBgBase: colors.background.default,
          colorBgContainer: colors.background.paper,
          colorBgElevated: colors.background.paper,
          colorBgLayout: colors.background.default,
          colorBgMask: 'rgba(0, 0, 0, 0.45)',
        },
        components: {
          Button: {
            colorPrimary: colors.primary.main,
            colorPrimaryHover: colors.primary.light,
            colorPrimaryActive: colors.primary.dark,
            colorPrimaryBg: colors.background.dark,
            colorPrimaryBgHover: colors.action.hover,
            colorPrimaryBorder: 'transparent',
            colorPrimaryBorderHover: 'transparent',
            borderRadius: 6,
            controlHeight: 40,
            controlHeightLG: 48,
            controlHeightSM: 32,
            boxShadow: 'none',
            boxShadowSecondary: 'none',
          },
          Input: {
            colorPrimary: colors.primary.main,
            colorPrimaryHover: colors.primary.light,
            colorPrimaryActive: colors.primary.dark,
            borderRadius: 6,
            controlHeight: 40,
            controlHeightLG: 48,
            controlHeightSM: 32,
            boxShadow: 'none',
          },
          Select: {
            colorPrimary: colors.primary.main,
            colorPrimaryHover: colors.primary.light,
            borderRadius: 6,
            controlHeight: 40,
            controlHeightLG: 48,
            controlHeightSM: 32,
            boxShadow: 'none',
          },
          Menu: {
            colorPrimary: colors.primary.main,
            itemSelectedBg: colors.action.selected,
            itemHoverBg: colors.action.hover,
            itemSelectedColor: colors.primary.main,
            itemColor: colors.text.secondary,
            itemHoverColor: colors.text.primary,
            boxShadow: 'none',
          },
          Card: {
            borderRadius: 8,
            colorBgContainer: colors.background.paper,
            colorBorderSecondary: 'transparent',
            boxShadow: 'none',
            boxShadowSecondary: 'none',
          },
          Drawer: {
            colorBgElevated: colors.background.paper,
            colorText: colors.text.primary,
            boxShadow: 'none',
          },
          Modal: {
            colorBgElevated: colors.background.paper,
            colorText: colors.text.primary,
            boxShadow: 'none',
          },
          Dropdown: {
            colorBgElevated: colors.background.paper,
            colorText: colors.text.primary,
            boxShadow: 'none',
          },
          Badge: {
            colorPrimary: colors.primary.main,
            colorSuccess: colors.success.main,
            colorWarning: colors.warning.main,
            colorError: colors.error.main,
            colorInfo: colors.info.main,
            boxShadow: 'none',
          },
        },
      }}
    >
    <AuthProvider>
        <AntApp>
          <AppContent />
        </AntApp>
    </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
