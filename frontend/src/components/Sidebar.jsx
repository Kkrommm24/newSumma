"use client"

import { useState } from "react"
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Input, Menu, ConfigProvider } from "antd"
import {
  SearchOutlined,
  HomeOutlined,
  FireOutlined,
  HeartOutlined,
  BookOutlined,
  UserOutlined,
  GlobalOutlined,
  BgColorsOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
} from "@ant-design/icons"
import logo from "../assets/images/logo.png"

const { Sider } = Layout

const gray100 = '#f3f4f6';
const gray200 = '#e5e7eb';
const gray800 = '#364254';
const gray600 = '#4b5563';

const Sidebar = ({ collapsed, onCollapse }) => {
  const [activeKey, setActiveKey] = useState('1')
  const navigate = useNavigate();

  const antdMenuItems = [
    { key: '1', icon: <HomeOutlined />, label: "Dành cho bạn", path: '/' },
    { key: '2', icon: <FireOutlined />, label: "Đang hot", path: '/trending' },
    { key: '3', icon: <HeartOutlined />, label: "Danh mục yêu thích", path: '/favourite-categories' },
    { key: '4', icon: <BookOutlined />, label: "Bookmark", path: '/bookmark' },
    { key: '5', icon: <UserOutlined />, label: "Trang cá nhân", path: '/profile' },
    { key: '6', icon: <GlobalOutlined />, label: "Ngôn ngữ", path: '/language' },
    { key: '7', icon: <BgColorsOutlined />, label: "Chủ đề", path: '/theme' },
  ]

  const handleMenuClick = (e) => {
    const clickedItem = antdMenuItems.find(item => item.key === e.key);
    if (clickedItem && clickedItem.path) {
      setActiveKey(e.key);
      navigate(clickedItem.path);
    }
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
              <Input
                placeholder="Tìm kiếm"
                prefix={<SearchOutlined />}
                className="bg-gray-100 border-none rounded-md focus:bg-white focus:ring-1 focus:ring-blue-500"
                style={{marginTop: '10px', marginBottom: '10px' }}
              />
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
              style={{marginTop: '80px', marginLeft: '15px'}}
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

