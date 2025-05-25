import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Input, Tag, Spin, Alert, Typography, Space, message, ConfigProvider, Button, Divider } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useSelector, useDispatch } from 'react-redux';
import {
  fetchFavoriteKeywords,
  addFavoriteKeyword,
  deleteFavoriteKeyword
} from '../store/slices/userSlice';
import { useAuth } from '../context/AuthContext.jsx';

const { Title, Text } = Typography;

// Danh sách từ khóa gợi ý (có thể lấy từ API sau này)
const suggestedKeywordsList = [
  'Công nghệ', 'Thể thao', 'Giải trí', 'Kinh tế', 'Thế giới',
  'Giáo dục', 'Sức khỏe', 'Du lịch', 'Xe', 'Bất động sản'
];

function FavouriteCategories() {
  const dispatch = useDispatch();
  const { isAuthenticated, authLoading } = useAuth();
  
  // Lấy state từ Redux
  const { 
      items: keywords, 
      status: keywordsStatus, 
      error: keywordsError 
  } = useSelector((state) => state.user.favoriteKeywords);
  
  const [newKeyword, setNewKeyword] = useState('');
  // Có thể giữ lại inputLoading hoặc dựa vào status của action add/delete nếu cần loading chi tiết hơn
  const [isAdding, setIsAdding] = useState(false); 

  // Fetch keywords khi component mount hoặc auth state thay đổi
  useEffect(() => {
    if (!authLoading && isAuthenticated && keywordsStatus === 'idle') {
      dispatch(fetchFavoriteKeywords());
    }
  }, [dispatch, authLoading, isAuthenticated, keywordsStatus]);

  const handleAddKeyword = async () => {
    const keywordToAdd = newKeyword.trim().toLowerCase(); // Chuẩn hóa thành chữ thường
    if (!keywordToAdd) {
      message.warning('Vui lòng nhập từ khóa.');
      return;
    }
    if (keywords.some(kw => kw.toLowerCase() === keywordToAdd)) {
        message.info(`Từ khóa "${newKeyword.trim()}" đã có trong danh sách.`);
        setNewKeyword('');
        return;
    }
    
    setIsAdding(true);
    try {
      // unwrap() sẽ trả về payload thành công hoặc throw lỗi nếu rejected
      await dispatch(addFavoriteKeyword(keywordToAdd)).unwrap(); 
      message.success(`Đã thêm từ khóa "${newKeyword.trim()}"`);
      setNewKeyword(''); 
    } catch (rejectedValue) {
      // Lỗi đã được log trong slice, có thể hiển thị thêm ở đây nếu muốn
      message.error(keywordsError || 'Lỗi khi thêm từ khóa!');
    } finally {
      setIsAdding(false);
    }
  };

  const handleAddSuggestedKeyword = async (keyword) => {
      const keywordToAdd = keyword.toLowerCase();
      if (keywords.some(kw => kw.toLowerCase() === keywordToAdd)) {
        message.info(`Từ khóa "${keyword}" đã có trong danh sách.`);
        return;
      }
       setIsAdding(true); // Có thể dùng loading chung cho các nút gợi ý
       try {
          await dispatch(addFavoriteKeyword(keywordToAdd)).unwrap();
          message.success(`Đã thêm từ khóa "${keyword}"`);
       } catch (rejectedValue) {
          message.error(keywordsError || 'Lỗi khi thêm từ khóa!');
       } finally {
         setIsAdding(false);
       }
  };

  const handleDeleteKeyword = async (keywordToDelete) => {
     const keywordLower = keywordToDelete.toLowerCase();
     try {
         await dispatch(deleteFavoriteKeyword(keywordLower)).unwrap();
         message.success(`Đã xóa từ khóa "${keywordToDelete}"`);
     } catch(rejectedValue) {
         message.error(keywordsError || 'Lỗi khi xóa từ khóa!');
     }
  };

  const availableSuggestions = suggestedKeywordsList.filter(
      suggestion => !keywords.some(kw => kw.toLowerCase() === suggestion.toLowerCase())
  );
  
  const isLoading = authLoading || keywordsStatus === 'loading' || keywordsStatus === 'idle';
  // Hiển thị lỗi từ Redux state
  const displayError = keywordsStatus === 'failed' ? keywordsError : null;

  return (
    <Row justify="center" style={{ padding: '20px' }}>
      <Col xs={24} sm={20} md={16} lg={12} xl={10}>
        <ConfigProvider
            theme={{
             token: {
               colorPrimary: '#252525',
             },
             components: {
               Button: {
                 colorPrimary: '#252525',
                 colorPrimaryHover: '#374151',
                 colorPrimaryActive: '#111827',
               },
               Input: {
                  colorPrimary: '#252525',
                  colorPrimaryHover: '#111827',
               },
               Alert: {
                 colorError: '#ff4d4f',
                 colorErrorBg: '#fff2f0',
                 colorErrorBorder: '#ffccc7'
               }
             }
           }}
        >
          <Title level={2} style={{ textAlign: 'center', marginBottom: '24px' }}>
            Từ khóa yêu thích
          </Title>
          
          <Text style={{ textAlign: 'center', display: 'block', marginBottom: '20px', color: 'gray' }}>
            Thêm các chủ đề bạn quan tâm để nhận được gợi ý tin tức phù hợp hơn.
          </Text>

          <Spin spinning={isLoading}> {/* Dùng isLoading */} 
            {displayError && !isLoading && ( /* Dùng displayError */
              <Alert 
                message="Lỗi" 
                description={ typeof displayError === 'string' ? displayError : 'Đã có lỗi xảy ra.'} 
                type="error" 
                showIcon 
                style={{ 
                  marginBottom: '16px',
                  backgroundColor: '#fff2f0',
                  borderColor: '#ffccc7',
                  color: '#ff4d4f'
                }} 
              />
            )}

            <Input.Search
               placeholder="Nhập từ khóa bạn yêu thích..."
              enterButton="Thêm"
              size="large"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onSearch={handleAddKeyword}
              loading={isAdding} // Dùng isAdding cho input search
              style={{ marginBottom: '24px' }}
              disabled={isLoading} // Disable khi đang tải lần đầu
            />
            
            {availableSuggestions.length > 0 && (
              <>
                 <Divider orientation="left" plain>Gợi ý cho bạn</Divider>
                 <Space size={[8, 8]} wrap style={{ marginBottom: '24px' }}>
                   {availableSuggestions.map((suggestion) => (
                     <Button 
                       key={suggestion}
                       icon={<PlusOutlined />}
                       size="small"
                       onClick={() => handleAddSuggestedKeyword(suggestion)}
                       disabled={isAdding} // Disable các nút gợi ý khi đang thêm
                     >
                       {suggestion}
                     </Button>
                   ))}
                 </Space>
              </>
            )}

            <Title level={4}>Danh sách của bạn:</Title>
            
            {keywords.length === 0 && !isLoading ? (
              <p style={{ color: 'grey' }}>Bạn chưa có từ khóa yêu thích nào.</p>
            ) : (
               <Space size={[8, 16]} wrap style={{ border: '1px solid #d9d9d9', padding: '16px', borderRadius: '8px', minHeight: '100px'}}>
                  {keywords.map((keyword) => (
                    <Tag
                      key={keyword}
                      closable
                      onClose={(e) => {
                        e.preventDefault();
                        handleDeleteKeyword(keyword);
                      }}
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
