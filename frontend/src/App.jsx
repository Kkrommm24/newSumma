import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from "antd"
import Sidebar from "./components/Sidebar"
import "./App.css"
import Home from './pages/Home';
import Trending from './pages/Trending';
import FavouriteCategories from './pages/FavouriteCategories';
import Bookmark from './pages/Bookmark';
import Profile from './pages/Profile';
import Language from './pages/Language';
import Theme from './pages/Theme';

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarExpandedWidth = 250;
  const sidebarCollapsedWidth = 80;

  const mainContentMarginLeft = collapsed ? sidebarCollapsedWidth : sidebarExpandedWidth;

  return (
    <BrowserRouter>
      <Layout className="min-h-screen">
        <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />
        <Layout style={{ marginLeft: mainContentMarginLeft, transition: 'margin-left 0.2s' }}>
          <main className="p-4 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/trending" element={<Trending />} />
              <Route path="/favourite-categories" element={<FavouriteCategories />} />
              <Route path="/bookmark" element={<Bookmark />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/language" element={<Language />} />
              <Route path="/theme" element={<Theme />} />
            </Routes>
          </main>
        </Layout>
      </Layout>
    </BrowserRouter>
  )
}

export default App;
