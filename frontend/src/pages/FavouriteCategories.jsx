import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Input, Tag, Spin, Alert, Typography, Space, message, ConfigProvider } from 'antd';
import axiosInstance from '../services/axiosInstance'; // Đảm bảo đường dẫn đúng
import { useAuth } from '../context/AuthContext.jsx'; // Import useAuth

const { Title } = Typography;

function FavouriteCategories() {
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inputLoading, setInputLoading] = useState(false); 
  const { isAuthenticated, authLoading } = useAuth(); 

  const fetchKeywords = useCallback(async () => {
    setError(null);
    try {
      const response = await axiosInstance.get('/user/fav-words');
      setKeywords(response.data.favorite_keywords || []);
    } catch (err) {
      console.error("Error fetching keywords:", err);
      setError('Không thể tải danh sách từ khóa yêu thích.');
      message.error('Lỗi tải danh sách từ khóa!');
    } finally {
       setLoading(false);
    }
  }, []);

  const handleAddKeyword = async () => {
    const keywordToAdd = newKeyword.trim();
    if (!keywordToAdd) {
      message.warning('Vui lòng nhập từ khóa.');
      return;
    }
    
    // Kiểm tra trùng lặp ở client trước khi gửi (không phân biệt hoa thường)
    if (keywords.some(kw => kw.toLowerCase() === keywordToAdd.toLowerCase())) {
        message.info(`Từ khóa "${keywordToAdd}" đã có trong danh sách.`);
        setNewKeyword(''); // Xóa input sau khi thông báo
        return;
    }

    setInputLoading(true);
    setError(null);
    try {
      // API PATCH cần body là { "keywords": [...] }
      const response = await axiosInstance.patch('/user/fav-words', { 
        keywords: [keywordToAdd] 
      });
      setKeywords(response.data.favorite_keywords || []);
      setNewKeyword('');
      message.success(`Đã thêm từ khóa "${keywordToAdd}"`);
    } catch (err) {
      console.error("Error adding keyword:", err);
      setError(`Không thể thêm từ khóa "${keywordToAdd}".`);
      message.error('Lỗi khi thêm từ khóa!');
    } finally {
      setInputLoading(false);
    }
  };

  const handleDeleteKeyword = async (keywordToDelete) => {
    setError(null);
    try {
      const response = await axiosInstance.delete('/user/fav-words', { 
        data: { keywords: [keywordToDelete] } 
      });
      setKeywords(response.data.favorite_keywords || []);
      message.success(`Đã xóa từ khóa "${keywordToDelete}"`);
    } catch (err) {
      console.error("Error deleting keyword:", err);
      setError(`Không thể xóa từ khóa "${keywordToDelete}".`);
      message.error('Lỗi khi xóa từ khóa!');
    }
  };

  // --- Effects --- 

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      setLoading(true);
      fetchKeywords();
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated, fetchKeywords]);

  // --- Render --- 

  return (
    <Row justify="center" style={{ padding: '20px' }}>
      <Col xs={24} sm={20} md={16} lg={12} xl={10}>
        <ConfigProvider
           theme={{
             token: {
               colorPrimary: '#1f2937', // Màu đen xám đậm
             },
             components: {
               Button: {
                 colorPrimary: '#1f2937',
                 colorPrimaryHover: '#111827',
                 colorPrimaryActive: '#000000',
               },
               Input: {
                  colorPrimary: '#1f2937',
                  colorPrimaryHover: '#111827',
               }
             }
           }}
        >
          <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>
            Từ khóa yêu thích
          </Title>

          <Spin spinning={loading || authLoading}>
            {error && !loading && !authLoading && (
              <Alert 
                message="Lỗi" 
                description={error} 
                type="error" 
                showIcon 
                style={{ marginBottom: '16px' }} 
              />
            )}

            <Input.Search
              placeholder="Nhập từ khóa bạn yêu thích..."
              enterButton="Thêm"
              size="large"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onSearch={handleAddKeyword}
              loading={inputLoading}
              style={{ marginBottom: '24px' }}
              disabled={loading || authLoading}
            />

            <Title level={4}>Danh sách từ khóa:</Title>
            
            {keywords.length === 0 && !loading && !authLoading ? (
              <p style={{ color: 'grey' }}>Bạn chưa có từ khóa yêu thích nào.</p>
            ) : (
               <Space size={[8, 16]} wrap style={{ border: '1px solid #d9d9d9', padding: '16px', borderRadius: '8px', minHeight: '100px'}}>
                  {keywords.map((keyword) => (
                    <Tag
                      key={keyword}
                      closable
                      onClose={(e) => {
                        e.preventDefault(); // Ngăn sự kiện mặc định nếu có
                        handleDeleteKeyword(keyword);
                      }}
                      // Bỏ màu xanh cứng, để theme hoặc màu mặc định xử lý
                      // color="blue" 
                      style={{ padding: '5px 10px', fontSize: '14px', margin: '4px' }}
                    >
                      {keyword}
                    </Tag>
                  ))}
               </Space>
            )}
          </Spin>
        </ConfigProvider>
      </Col>
    </Row>
  );
}

export default FavouriteCategories;
