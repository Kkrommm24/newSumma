import React, { useEffect, useState } from 'react';
import { List, Spin, Typography, Alert, Row, Col, Empty, App, Input, Button, Modal, Checkbox, Space } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useSelector, useDispatch } from 'react-redux';
import { fetchBookmarks, removeBookmark } from '../store/slices/userSlice';
import NewsCard from '../components/NewsCard';
import { useAuth } from '../context/AuthContext.jsx';

const { Title, Text } = Typography;
const { confirm } = Modal;

function Bookmark() {
  const dispatch = useDispatch();
  const { message } = App.useApp();
  const { isAuthenticated, authLoading } = useAuth();

  const { 
    items: bookmarks, 
    status: bookmarksStatus, 
    error: bookmarksError 
  } = useSelector((state) => state.user.bookmarks);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBookmarks, setSelectedBookmarks] = useState([]);
  const [isSelecting, setIsSelecting] = useState(false);

  useEffect(() => {
    if (!authLoading && isAuthenticated && bookmarksStatus === 'idle') {
      dispatch(fetchBookmarks());
    }
  }, [dispatch, authLoading, isAuthenticated, bookmarksStatus]);

  const handleRemoveBookmark = (articleId) => {
    dispatch(removeBookmark(articleId))
      .unwrap()
      .then(() => {
        message.success('Đã xóa bài viết khỏi bookmark.');
        setSelectedBookmarks(prev => prev.filter(id => id !== articleId));
      })
      .catch(() => {
        message.error(bookmarksError || 'Lỗi khi xóa bookmark.');
      });
  };

  const showDeleteConfirm = (articleId) => {
    confirm({
      title: 'Bạn có chắc muốn xóa bookmark này?',
      icon: <DeleteOutlined />,
      content: 'Hành động này không thể hoàn tác.',
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      onOk() {
        handleRemoveBookmark(articleId);
      },
    });
  };

  const handleSelectChange = (articleId, checked) => {
    setSelectedBookmarks(prev => 
      checked ? [...prev, articleId] : prev.filter(id => id !== articleId)
    );
  };

  const showBulkDeleteConfirm = () => {
    if (selectedBookmarks.length === 0) {
      message.warning('Vui lòng chọn ít nhất một bài viết để xóa.');
      return;
    }
    confirm({
      title: `Bạn có chắc muốn xóa ${selectedBookmarks.length} bookmark đã chọn?`,
      icon: <DeleteOutlined />,
      content: 'Hành động này không thể hoàn tác.',
      okText: 'Xóa tất cả',
      okType: 'danger',
      cancelText: 'Hủy',
      async onOk() {
        let successCount = 0;
        let errorCount = 0;
        const deletePromises = selectedBookmarks.map(id => 
            dispatch(removeBookmark(id)).unwrap()
        );
        
         try {
            await Promise.all(deletePromises);
            successCount = selectedBookmarks.length;
         } catch (error) {
            console.error("Error during bulk delete (one or more failed):", error);
            dispatch(fetchBookmarks()); 
            errorCount = selectedBookmarks.length - (await dispatch(fetchBookmarks()).unwrap().length);
         }

        if (successCount > 0) {
           message.success(`Đã xóa thành công ${successCount} bookmark.`);
        }
        if (errorCount > 0) {
             message.error(`Xóa thất bại ${errorCount} bookmark. Vui lòng thử lại.`);
        }
        setSelectedBookmarks([]);
        setIsSelecting(false);
      },
    });
  };
  
  const filteredBookmarks = bookmarks.filter(item => 
    item?.title?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    item?.summary?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isLoading = authLoading || bookmarksStatus === 'loading' || bookmarksStatus === 'idle';
  const displayError = bookmarksStatus === 'failed' ? bookmarksError : null;

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>Bài viết đã lưu</Title>
      
       <Row justify="space-between" align="middle" style={{ marginBottom: '20px' }}>
           <Col xs={24} sm={12} md={10} lg={8}>
               <Input.Search 
                   placeholder="Tìm kiếm trong bookmark..." 
                   onChange={(e) => setSearchTerm(e.target.value)} 
                   allowClear
                   style={{ width: '100%' }}
                   disabled={isLoading}
               />
           </Col>
           <Col>
               <Space>
                   {isSelecting && (
                       <Button 
                           danger 
                           icon={<DeleteOutlined />} 
                           onClick={showBulkDeleteConfirm}
                           disabled={selectedBookmarks.length === 0}
                       >
                           Xóa ({selectedBookmarks.length})
                       </Button>
                   )}
                   <Button onClick={() => setIsSelecting(!isSelecting)} disabled={isLoading || filteredBookmarks.length === 0}>
                       {isSelecting ? 'Hủy chọn' : 'Chọn để xóa'}
                   </Button>
               </Space>
           </Col>
       </Row>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>
      ) : displayError ? (
        <Alert message="Lỗi" description={typeof displayError === 'string' ? displayError : 'Không thể tải bookmark.'} type="error" showIcon />
      ) : filteredBookmarks.length === 0 ? (
         searchTerm ? (
             <Empty description={<Text>Không tìm thấy bookmark nào khớp với "{searchTerm}".</Text>} />
         ) : (
             <Empty description="Bạn chưa lưu bài viết nào."/>
         )
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 3, xl: 3, xxl: 4 }}
          dataSource={filteredBookmarks}
          renderItem={(item) => (
            <List.Item key={item.id} style={{ position: 'relative' }}>
                {isSelecting && (
                  <Checkbox 
                     checked={selectedBookmarks.includes(item.id)}
                     onChange={(e) => handleSelectChange(item.id, e.target.checked)}
                     style={{ position: 'absolute', top: 10, left: 10, zIndex: 1, background: 'rgba(255,255,255,0.8)', borderRadius: '4px', padding: '2px'}}
                  />
                 )} 
              <NewsCard
                 id={item.id}
                 title={item.title}
                 summary={item.summary_text || item.summary}
                 imageUrl={item.image_url}
                 sourceUrl={item.url}
                 publishedAt={item.published_at}
                 showBookmarkButton={!isSelecting}
                 isBookmarked={true}
                 onBookmarkToggle={() => showDeleteConfirm(item.id)}
              />
               {!isSelecting && (
                  <Button 
                     icon={<DeleteOutlined />} 
                     onClick={() => showDeleteConfirm(item.id)} 
                     danger 
                     type="primary" 
                     shape="circle" 
                     size="small"
                     style={{ position: 'absolute', top: 10, right: 10, zIndex: 1 }}
                  />
               )}
            </List.Item>
          )}
        />
      )}
    </div>
  );
}

export default Bookmark;
