"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { useNavigate, useLocation } from 'react-router-dom';
import { Layout, Button, Input, Menu, ConfigProvider, Dropdown, Spin, List, Typography, App } from "antd"
import {
  SearchOutlined,
  HomeOutlined,
  FireOutlined,
  HeartOutlined,
  BookOutlined,
  UserOutlined,
  BgColorsOutlined,
  LogoutOutlined,

  CloseOutlined
} from "@ant-design/icons"
import logo from "../assets/images/logo.png"
import { useAuth } from '../context/AuthContext.jsx';
import { useSelector, useDispatch } from 'react-redux';
import {
  fetchSearchHistory,
  addSearchHistory,
  deleteSearchHistoryItem,
  resetUserState
} from '../store/slices/userSlice';

const { Sider } = Layout
const { Text } = Typography;

const gray100 = '#f3f4f6';
const gray200 = '#e5e7eb';
const gray800 = '#364254';
const gray600 = '#4b5563';

const Sidebar = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { logout: authLogout, isAuthenticated, authLoading } = useAuth();
  const { message } = App.useApp();

  const { 
      items: searchHistory, 
      status: historyStatus, 
  } = useSelector((state) => state.user.searchHistory);

  const [searchTerm, setSearchTerm] = useState('');
  const [isHistoryVisible, setIsHistoryVisible] = useState(false);
  const inputRef = useRef(null);
  
  const loadingHistory = historyStatus === 'loading';

  const antdMenuItems = [
    { key: '1', icon: <HomeOutlined />, label: "Dành cho bạn", path: '/' },
    { key: '2', icon: <FireOutlined />, label: "Đang hot", path: '/trending' },
    { key: '3', icon: <HeartOutlined />, label: "Danh mục yêu thích", path: '/favourite-categories' },
    { key: '4', icon: <BookOutlined />, label: "Bookmark", path: '/bookmark' },
    { key: '5', icon: <UserOutlined />, label: "Trang cá nhân", path: '/profile' }
  ]

  const getKeyFromPath = (pathname) => {
    const currentItem = antdMenuItems.find(item => item.path === pathname);
    return currentItem ? currentItem.key : '1';
  }

  const [activeKey, setActiveKey] = useState(getKeyFromPath(location.pathname));

  useEffect(() => {
    if (!authLoading && isAuthenticated && historyStatus === 'idle') {
      dispatch(fetchSearchHistory())
        .unwrap()
        .catch((error) => {
          console.error("Failed to fetch search history:", error);
          message.error("Không thể tải lịch sử tìm kiếm.");
        });
    }
  }, [dispatch, authLoading, isAuthenticated, historyStatus]);

  const handleAddSearchHistory = (query) => {
    if (!isAuthenticated || !query || !query.trim()) return;
    dispatch(addSearchHistory(query.trim()))
        .unwrap()
        .catch((rejectedValue) => {
            console.error("Failed to add search history:", rejectedValue);
            message.error("Lỗi khi lưu lịch sử tìm kiếm.");
        });
  };

  const handleDeleteSearchHistoryItem = (queryToDelete) => {
    if (!isAuthenticated) return;
    dispatch(deleteSearchHistoryItem(queryToDelete))
        .unwrap()
        .then(() => {
            message.success(`Đã xóa "${queryToDelete}" khỏi lịch sử.`);
        })
        .catch((rejectedValue) => {
            console.error("Failed to delete search history:", rejectedValue);
            message.error("Lỗi khi xóa lịch sử tìm kiếm.");
        });
  };

  const handleSearch = (value) => {
    const query = value.trim();
    if (!query) return;
    setSearchTerm(query);
    handleAddSearchHistory(query);
    setIsHistoryVisible(false);
    inputRef.current?.blur();
    navigate(`/?q=${encodeURIComponent(query)}`);
  };

  useEffect(() => {
    setActiveKey(getKeyFromPath(location.pathname));
  }, [location.pathname]);

  const handleMenuClick = (e) => {
    const clickedItem = antdMenuItems.find(item => item.key === e.key);
    if (clickedItem && clickedItem.path) {
      navigate(clickedItem.path);
    }
  };
  
  const handleLogout = () => {
    authLogout();
    dispatch(resetUserState());
  };

  const getHistoryMenuItems = () => {
    if (loadingHistory) {
        return [{ key: 'loading', label: <div className="text-center p-3"><Spin size="small" /></div>, disabled: true }];
    }

    if (!Array.isArray(searchHistory) || searchHistory.length === 0) {
        return [{ key: 'no-history', label: <div className="p-3 text-center text-gray-500">Không có lịch sử tìm kiếm.</div>, disabled: true }];
    }

    const uniqueQueries = new Set();
    const uniqueSearchHistory = searchHistory.filter(item => {
      if (item && item.query && !uniqueQueries.has(item.query.toLowerCase())) {
        uniqueQueries.add(item.query.toLowerCase());
        return true;
      }
      return false;
    });

    return uniqueSearchHistory.map((item) => ({
      key: item.id || item.query,
      label: (
        <div className="flex justify-between items-center w-full">
          <Text
            className="truncate flex-grow mr-2 cursor-pointer"
            onClick={() => handleSearch(item.query)}
          >
            {item.query}
          </Text>
          <Button
            type="text"
            icon={<CloseOutlined className="text-gray-500 hover:text-red-500" />}
            size="small"
            style={{ flexShrink: 0 }}
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteSearchHistoryItem(item.query);
            }}
          />
        </div>
      ),
    }));
  };

  return (
    
    <ConfigProvider
      theme={{
        components: {
          Menu: {
            itemSelectedBg: gray100,
            itemHoverBg: gray200,
            itemSelectedColor: gray800,
            itemColor: gray600,
            itemHoverColor: gray600,
          },
        },
      }}
    >
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={onCollapse}
        className="bg-white shadow-md"
        width={250}
        theme="light"
        breakpoint="lg"
        collapsedWidth={80}
        style={{
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          transition: 'width 0.2s ease-in-out',
          overflow: 'hidden',
        }}
      >
        <div className={`p-4 h-16 flex items-center ${collapsed ? 'justify-center' : ''}`}>
          <img
            src={logo}
            alt="Logo"
            className={`transition-all duration-300 max-w-full ${collapsed ? 'h-6 w-auto' : 'h-8 w-auto'}`}
            width={collapsed ? 80 : 250}
          />
        </div>

        <div className="flex flex-col flex-grow justify-between h-[calc(100vh-64px)]" style={{ marginLeft: '10px', marginRight: '10px' }}>
          <div className="flex flex-col">
            <div className="px-4 py-2 mb-2">
              <Dropdown
                menu={{ items: getHistoryMenuItems() }}
                open={isHistoryVisible}
                placement="bottomLeft"
                dropdownRender={(menu) => (
                  <div
                    className="shadow-lg rounded-md border border-gray-200 bg-white"
                     style={{
                        width: inputRef.current?.offsetWidth,
                        maxHeight: '240px',
                        overflowY: 'auto'
                     }}
                  >
                    {menu}
                  </div>
                )}
              >
                <Input
                  ref={inputRef}
                  placeholder="Tìm kiếm"
                  prefix={<SearchOutlined />}
                  className="bg-gray-100 border-none rounded-md focus:bg-white focus:ring-1 focus:ring-blue-500"
                  style={{marginTop: '10px', marginBottom: '10px' }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onFocus={() => {
                     setIsHistoryVisible(true);
                  }}
                  onBlur={() => {
                      setTimeout(() => {
                          setIsHistoryVisible(false);
                      }, 150);
                  }}
                  onPressEnter={(e) => {
                      handleSearch(e.target.value);
                  }}
                />
              </Dropdown>
            </div>

            <Menu
              theme="light"
              mode="inline"
              selectedKeys={[activeKey]}
              items={antdMenuItems}
              onClick={handleMenuClick}
              className="border-r-0"
            />
          </div>

          <div className="mb-4 px-4">
            <Button
              danger
              icon={<LogoutOutlined />}
              className="w-full flex items-center justify-center"
              style={{
                marginTop: '80px', 
                marginLeft: '15px',
                boxShadow: 'none'
              }}
              onClick={handleLogout}
            >
              {!collapsed && "Logout"}
            </Button>
          </div>
        </div>
      </Sider>
    </ConfigProvider>
  )
}

export default Sidebar

