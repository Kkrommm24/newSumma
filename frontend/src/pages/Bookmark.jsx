import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { List, Spin, Typography, Alert, Row, Col, Empty, App, Input, Button, Modal, Space, Select, DatePicker, Card } from 'antd';
import { DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useSelector, useDispatch } from 'react-redux';
import { fetchBookmarks, removeBookmark } from '../store/slices/userSlice';
import NewsCard from '../components/NewsCard';
import { useAuth } from '../context/AuthContext.jsx';
import axiosInstance from '../services/axiosInstance';
import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';

dayjs.extend(isBetween);

const { Title, Text, Link } = Typography;
const { confirm } = Modal;
const { Option } = Select;
const { RangePicker } = DatePicker;

const formatDate = (dateString) => {
   if (!dateString) return 'N/A';
   return dayjs(dateString).format('DD/MM/YYYY HH:mm');
}

function Bookmark() {
  const dispatch = useDispatch();
  const { message, modal } = App.useApp();
  const { isAuthenticated, authLoading } = useAuth();

  const { 
    items: bookmarks, 
    status: bookmarksStatus, 
    error: bookmarksError 
  } = useSelector((state) => state.user.bookmarks);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedArticleSummary, setSelectedArticleSummary] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const [filterCategory, setFilterCategory] = useState(null);
  const [filterDateRange, setFilterDateRange] = useState([null, null]);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      dispatch(fetchBookmarks());
    }
  }, [dispatch, authLoading, isAuthenticated]);

  const fetchSummaryForArticle = useCallback(async (articleId) => {
    if (!articleId) return;
    setDetailLoading(true);
    setDetailError(null);
    setSelectedArticleSummary(null); 
    try {
      const response = await axiosInstance.get(`/news/articles/${articleId}`);
      setSelectedArticleSummary(response.data);
    } catch (err) {
      console.error(`Error fetching summary for article ${articleId}:`, err);
      if (err.response && err.response.status === 404) {
        setDetailError("Không tìm thấy tóm tắt cho bài viết này.");
      } else {
        setDetailError("Lỗi khi tải chi tiết tóm tắt.");
      }
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const handleRemoveBookmark = (articleId) => {
    dispatch(removeBookmark(articleId))
      .unwrap()
      .then(() => {
        message.success('Đã xóa bài viết khỏi bookmark.');
        handleBackToList();
      })
      .catch((error) => {
        console.error('[Bookmark] removeBookmark dispatch failed:', error);
        const errorMessage = error?.message || bookmarksError || 'Lỗi khi xóa bookmark.';
        message.error(errorMessage);
      });
  };

  const showDeleteConfirm = (articleId, articleTitle) => {
    modal.confirm({
      title: `Xóa bookmark "${articleTitle}"?`,
      icon: <DeleteOutlined style={{ color: 'red' }}/>,
      content: 'Hành động này không thể hoàn tác.',
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      onOk() {
        handleRemoveBookmark(articleId);
      },
      onCancel() {
      }
    });
  };

  const availableCategories = useMemo(() => {
    const categories = new Map();
    bookmarks.forEach(item => {
      if (item?.article?.categories) {
        item.article.categories.forEach(cat => {
          if (cat && cat.id && cat.name) {
            categories.set(cat.id, cat.name);
          }
        });
      }
    });
    return Array.from(categories.entries()).map(([id, name]) => ({ id, name }));
  }, [bookmarks]);
  
  const filteredBookmarks = useMemo(() => {
      let items = bookmarks.filter(item => item && item.article);
      
      if (searchTerm) {
          items = items.filter(item => 
            item.article.title?.toLowerCase().includes(searchTerm.toLowerCase()) || 
            item.article.summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.article.summary_text?.toLowerCase().includes(searchTerm.toLowerCase())
          );
      }
      
      if (filterCategory) {
          items = items.filter(item => 
            item.article.categories?.some(cat => cat && cat.id === filterCategory)
          );
      }
      
      const [startDate, endDate] = filterDateRange;
      if (startDate && endDate) {
          items = items.filter(item => {
              if (!item.article.published_at) return false;
              const publishedDate = dayjs(item.article.published_at);
              return publishedDate.isBetween(startDate, endDate.add(1, 'day'), null, '[)');
          });
      }
      
      return items;
  }, [bookmarks, searchTerm, filterCategory, filterDateRange]);
  
  const handleTitleClick = (article) => {
    setSelectedArticle(article);
    fetchSummaryForArticle(article.id);
  };

  const handleBackToList = () => {
    setSelectedArticle(null);
    setSelectedArticleSummary(null);
    setDetailError(null);
  };

  const handleCategoryFilterChange = (value) => {
    if (value === filterCategory) {
        setFilterCategory(null);
    } else {
        setFilterCategory(value);
    }
  };

  const handleDateFilterChange = (dates) => {
    if (dates && dates.length === 2) {
      setFilterDateRange([dates[0], dates[1]]);
    } else {
      setFilterDateRange([null, null]);
    }
  };

  const isLoading = authLoading || bookmarksStatus === 'loading' || bookmarksStatus === 'idle';
  const displayError = bookmarksStatus === 'failed' ? bookmarksError : null;
  
  if (selectedArticle) {
      const newsCardData = selectedArticleSummary ? {
          id: selectedArticleSummary.id,
          articleId: selectedArticle.id,
          title: selectedArticleSummary.title || selectedArticle.title,
          summary: selectedArticleSummary.summary_text,
          imageUrl: selectedArticleSummary.image_url || selectedArticle.image_url,
          sourceUrl: selectedArticleSummary.url || selectedArticle.url,
          keywords: selectedArticleSummary.keywords || [],
          publishedAt: selectedArticleSummary.published_at || selectedArticle.published_at,
          userVote: selectedArticleSummary.user_vote === true ? true : selectedArticleSummary.user_vote === false ? false : null,
          upvotes: selectedArticleSummary.upvotes,
          downvotes: selectedArticleSummary.downvotes,
          isBookmarked: true
      } : {
          id: selectedArticle.id,
          articleId: selectedArticle.id,
          title: selectedArticle.title,
          summary: 'Đang tải tóm tắt...',
          imageUrl: selectedArticle.image_url,
          sourceUrl: selectedArticle.url,
          keywords: [],
          publishedAt: selectedArticle.published_at,
          userVote: null,
          upvotes: 0,
          downvotes: 0,
          isBookmarked: true
      };
      
      if (detailError && !selectedArticleSummary) {
          newsCardData.summary = detailError;
      }
      
      return (
          <div className="p-4 md:p-8">
              <Button 
                  type="text" 
                  icon={<ArrowLeftOutlined />} 
                  onClick={handleBackToList} 
                  className="mb-4"
              >
                  Quay lại danh sách
              </Button>
              <Row justify="center" style={{ paddingTop: '0', paddingBottom: '2rem' }}>
                  <Col style={{ maxWidth: '600px', width: '100%' }}>
                      {detailLoading && <div className="text-center py-10"><Spin tip="Đang tải chi tiết..." /></div>}
                      {!detailLoading && (
                          <NewsCard
                              {...newsCardData}
                              showBookmarkButton={true}
                              onBookmarkToggle={(articleIdFromCard, isBookmarkedFromCard) => {
                                  if (articleIdFromCard && isBookmarkedFromCard) {
                                      showDeleteConfirm(articleIdFromCard, selectedArticle.title);
                                  } else {
                                      message.error('Không thể thực hiện thao tác này.');
                                  }
                              }}
                          />
                      )}
                      {detailError && !detailLoading && (
                          <div className="mt-4 text-center">
                              <Alert message="Lỗi" description={detailError} type="error" showIcon />
                          </div>
                      )}
                  </Col>
              </Row>
          </div>
      );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>Bài viết đã lưu</Title>
      
       <Row justify="start" align="middle" gutter={[16, 16]} style={{ marginBottom: '20px' }}>
           <Col xs={24} sm={12} md={8} lg={6}>
               <Input.Search 
                   placeholder="Tìm kiếm..." 
                   onChange={(e) => setSearchTerm(e.target.value)} 
                   allowClear
                   style={{ width: '100%' }}
                   disabled={isLoading}
               />
           </Col>
           <Col xs={12} sm={6} md={4} lg={4}>
                <div 
                    className={`transition-opacity duration-200 ease-in-out ${ 
                    filterCategory ? 'opacity-80' : 'opacity-100 hover:opacity-80' 
                    }`}
                    style={{width: '100%'}}
                >
                    <Select
                        placeholder="Danh mục"
                        allowClear
                        style={{ width: '100%' }}
                        onChange={handleCategoryFilterChange}
                        value={filterCategory}
                        disabled={isLoading || availableCategories.length === 0}
                    >
                        {availableCategories.map(cat => (
                            <Option key={cat.id} value={cat.id}>{cat.name}</Option>
                        ))}
                    </Select>
                </div>
           </Col>
           <Col xs={12} sm={6} md={6} lg={6}>
                <div 
                    className={`transition-opacity duration-200 ease-in-out ${ 
                    filterDateRange[0] && filterDateRange[1] ? 'opacity-80' : 'opacity-100 hover:opacity-80' 
                    }`}
                     style={{width: '100%'}}
                >
                    <RangePicker 
                        placeholder={['Từ ngày', 'Đến ngày']}
                        onChange={handleDateFilterChange} 
                        format="DD/MM/YYYY"
                        style={{ width: '100%' }}
                        disabled={isLoading}
                    />
                </div>
           </Col>
       </Row>

      <Card>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>
          ) : displayError ? (
            <Alert message="Lỗi" description={typeof displayError === 'string' ? displayError : 'Không thể tải bookmark.'} type="error" showIcon />
          ) : filteredBookmarks.length === 0 ? (
            searchTerm || filterCategory || filterDateRange[0] ? ( 
                <Empty description={<Text>Không tìm thấy bookmark nào phù hợp.</Text>} />
            ) : (
                <Empty description="Bạn chưa lưu bài viết nào."/>
            )
          ) : (
            <List
              itemLayout="horizontal"
              dataSource={filteredBookmarks}
              renderItem={(item) => {
                 if (!item || !item.article) return null;
                 const article = item.article;
                 return (
                    <List.Item 
                        key={article.id}
                        actions={[
                            <Button 
                                icon={<DeleteOutlined />} 
                                type="text" 
                                danger 
                                onClick={() => showDeleteConfirm(article.id, article.title)}
                            />
                        ]}
                    >
                        <List.Item.Meta
                            title={<Link onClick={() => handleTitleClick(article)} className="text-base hover:text-blue-600">{article.title || 'Không có tiêu đề'}</Link>}
                            description={<Text type="secondary" style={{ fontSize: '12px' }}>Xuất bản: {formatDate(article.published_at)} | <a href={article.url} target="_blank" rel="noopener noreferrer">Đọc bài gốc</a></Text>}
                        />
                    </List.Item>
                  );
                }
              }
            />
          )}
      </Card>
    </div>
  );
}

export default Bookmark;
