import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Spin, Select, DatePicker, Button, Card, List, Typography, Space, Alert, Empty, Row, Col } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';
import axiosInstance from '../services/axiosInstance';
import NewsCard from '../components/NewsCard';

dayjs.extend(isBetween);

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text, Link } = Typography;

function Bookmark() {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedArticleSummary, setSelectedArticleSummary] = useState(null);

  const [filterCategory, setFilterCategory] = useState(null);
  const [filterDateRange, setFilterDateRange] = useState([null, null]);

  const fetchBookmarks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get('/user/bookmarks');
      const validBookmarks = response.data
        .map(b => b.article)
        .filter(article => article !== null && article !== undefined); 
      setBookmarks(validBookmarks);
    } catch (err) {
      console.error("Error fetching bookmarks:", err);
      setError("Không thể tải danh sách bookmark. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBookmarks();
  }, [fetchBookmarks]);

  const fetchSummaryForArticle = useCallback(async (articleId) => {
    if (!articleId) return;
    setDetailLoading(true);
    setDetailError(null);
    setSelectedArticleSummary(null);
    try {
      const response = await axiosInstance.get(`/news/articles/${articleId}/summary/`);
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


  const availableCategories = useMemo(() => {
    const categories = new Map();
    bookmarks.forEach(article => {
      if (article?.categories) {
        article.categories.forEach(cat => {
          if (cat && cat.id && cat.name) {
            categories.set(cat.id, cat.name);
          }
        });
      }
    });
    return Array.from(categories.entries()).map(([id, name]) => ({ id, name }));
  }, [bookmarks]);

  const filteredBookmarks = useMemo(() => {
    let items = [...bookmarks];

    if (filterCategory) {
      items = items.filter(article => 
        article.categories?.some(cat => cat && cat.id === filterCategory)
      );
    }

    const [startDate, endDate] = filterDateRange;
    if (startDate && endDate) {
      items = items.filter(article => {
        if (!article.published_at) return false;
        const publishedDate = dayjs(article.published_at);
        return publishedDate.isBetween(startDate, endDate.add(1, 'day'), null, '[)'); 
      });
    }

    return items;
  }, [bookmarks, filterCategory, filterDateRange]);

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
  
  const formatDate = (dateString) => {
     if (!dateString) return 'N/A';
     return dayjs(dateString).format('DD/MM/YYYY HH:mm');
  }

  if (loading) {
    return <div className="flex justify-center items-center h-screen"><Spin size="large" /></div>;
  }

  if (error) {
    return <div className="p-4"><Alert message="Lỗi" description={error} type="error" showIcon /></div>;
  }

  if (selectedArticle) {
    const newsCardData = selectedArticleSummary ? {
      id: selectedArticleSummary.id,
      title: selectedArticleSummary.title || selectedArticle.title,
      summary: selectedArticleSummary.summary_text,
      imageUrl: selectedArticleSummary.image_url || selectedArticle.image_url,
      sourceUrl: selectedArticleSummary.url || selectedArticle.url,
      keywords: selectedArticleSummary.keywords || [],
      publishedAt: selectedArticleSummary.published_at || selectedArticle.published_at,
      userVote: selectedArticleSummary.user_vote === true ? true : selectedArticleSummary.user_vote === false ? false : null,
      upvotes: selectedArticleSummary.upvotes,
      downvotes: selectedArticleSummary.downvotes
    } : {
      id: selectedArticle.id,
      title: selectedArticle.title,
      summary: 'Đang tải tóm tắt...',
      imageUrl: selectedArticle.image_url,
      sourceUrl: selectedArticle.url,
      keywords: [],
      publishedAt: selectedArticle.published_at,
      userVote: null,
      upvotes: 0,
      downvotes: 0
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
                 id={newsCardData.id}
                 title={newsCardData.title}
                 summary={newsCardData.summary}
                 imageUrl={newsCardData.imageUrl}
                 sourceUrl={newsCardData.sourceUrl}
                 publishedAt={newsCardData.publishedAt}
                 isSelected={true}
                 userVote={newsCardData.userVote}
                 upvotes={newsCardData.upvotes}
                 downvotes={newsCardData.downvotes}
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

  // List View Rendering
  return (
    <div className="p-4 md:p-8">
      <div className="bg-white p-6 rounded-lg shadow-md">
          <Card className="mb-6 border-0 shadow-none" style ={{ marginTop: '5vh' }}>
            <Space wrap>
              <div 
                className={`transition-opacity duration-200 ease-in-out ${ 
                  filterCategory ? 'opacity-80' : 'opacity-100 hover:opacity-80' 
                }`}
              >
                <Select
                  placeholder="Lọc theo danh mục"
                  allowClear
                  style={{ width: 200 }}
                  onChange={handleCategoryFilterChange}
                  value={filterCategory}
                  disabled={availableCategories.length === 0}
                >
                  {availableCategories.map(cat => (
                    <Option key={cat.id} value={cat.id}>{cat.name}</Option>
                  ))}
                </Select>
              </div>
              <div 
                className={`transition-opacity duration-200 ease-in-out ${ 
                  filterDateRange[0] && filterDateRange[1] ? 'opacity-80' : 'opacity-100 hover:opacity-80' 
                }`}
                style ={{ marginLeft: '3vh' }}
              >
                <RangePicker 
                  placeholder={['Từ ngày', 'Đến ngày']}
                  onChange={handleDateFilterChange} 
                  format="DD/MM/YYYY"
                />
              </div>
            </Space>
          </Card>

          {/* Card chứa Bookmarks List hoặc Empty state */}
          <Card className="border-0 shadow-none" style ={{ marginTop: '3vh' }}>
              {filteredBookmarks.length > 0 ? (
                <List
                  itemLayout="horizontal"
                  dataSource={filteredBookmarks}
                  renderItem={article => (
                    <List.Item
                      actions={[<Link href={article.url} target="_blank" rel="noopener noreferrer">Đọc bài gốc</Link>]}
                    >
                      <List.Item.Meta
                        title={<Link onClick={() => handleTitleClick(article)} className="text-lg">{article.title || 'Không có tiêu đề'}</Link>}
                        description={`Xuất bản: ${formatDate(article.published_at)}`}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description={bookmarks.length === 0 ? "Bạn chưa lưu bài viết nào." : "Không có kết quả nào phù hợp với bộ lọc."} />
              )}
           </Card>
      </div>
    </div>
  );
}

export default Bookmark;
