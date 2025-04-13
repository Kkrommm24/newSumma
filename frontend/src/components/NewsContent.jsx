import React, { useState, useEffect, useRef, useCallback } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Spin } from 'antd';
import NewsCard from "./NewsCard";
import axiosInstance from '../services/axiosInstance';

const NEWS_PER_PAGE = 10;

const NewsContent = ({ fetchMode = 'recommendations' }) => {
  const [newsItems, setNewsItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCardId, setSelectedCardId] = useState(null);
  const cardRefs = useRef({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchNews = useCallback(async (pageToFetch) => {
    if (pageToFetch === 1) {
      setLoading(true);
    }
    setError(null);
    
    let url = '';
    let params = {};

    try {
      if (fetchMode === 'trending') {
        url = `/summarizer/summaries/`;
        params = {
           sort_by: '-created_at',
           page: pageToFetch,
           page_size: NEWS_PER_PAGE
        }
      } else {
        const currentOffset = (pageToFetch - 1) * NEWS_PER_PAGE;
        url = `/recommender/recommendations/`;
        params = {
            limit: NEWS_PER_PAGE,
            offset: currentOffset
        }
      }
      
      console.log(`Fetching data from: ${url} with params:`, params);
      const response = await axiosInstance.get(url, { params });
      const data = response.data;

      if (data && data.results) {
        const formattedData = data.results.map(item => ({
          id: item.id,
          title: item.title || 'Không có tiêu đề',
          summary: item.summary_text || item.summary || 'Không có tóm tắt',
          imageUrl: item.image_url || null,
          sourceUrl: item.url || '#',
          keywords: item.keywords || []
        }));

        setNewsItems(prevItems =>
          pageToFetch === 1 ? formattedData : [...prevItems, ...formattedData]
        );
        setTotalCount(data.count || 0);
        setHasMore((pageToFetch * NEWS_PER_PAGE) < (data.count || 0));
        setCurrentPage(pageToFetch + 1);

      } else {
        setHasMore(false);
        if (pageToFetch === 1) setNewsItems([]);
        console.warn("API response structure might be different:", data);
      }
    } catch (err) {
      console.error("Error fetching news:", err);
      let errorMessage = err.message;
      try {
        const parsedError = JSON.parse(err.message);
        errorMessage = `HTTP error! Status: ${parsedError.status} - ${parsedError.message}. Body: ${parsedError.body?.substring(0, 100) || 'N/A'}`;
      } catch (parseError) {}
      setError(errorMessage);
      setHasMore(false);
    } finally {
      if (pageToFetch === 1) {
        setLoading(false);
      }
    }
  }, [fetchMode]);

  useEffect(() => {
    setNewsItems([]);
    setCurrentPage(1);
    setHasMore(true);
    fetchNews(1);
  }, [fetchMode, fetchNews]);

  useEffect(() => {
    if (selectedCardId && cardRefs.current[selectedCardId]) {
        cardRefs.current[selectedCardId].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
  }, [selectedCardId]);

  const fetchMoreData = () => {
    if (!hasMore || loading) return;
    fetchNews(currentPage);
  };

  const handleCardClick = (id) => {
    setSelectedCardId(id);
  };

  if (loading) {
    return <div className="text-center py-10"><Spin size="large" /></div>;
  }

  if (error && newsItems.length === 0) {
    return <div className="text-red-600 bg-red-100 p-4 rounded text-center">Lỗi tải tin tức: {error}</div>;
  }

  if (!loading && newsItems.length === 0 && !hasMore) {
    return <div className="text-center py-10 text-gray-500">Không có tin tức nào để hiển thị.</div>;
  }

  return (
    <div className="relative min-h-screen">
      <InfiniteScroll
        dataLength={newsItems.length}
        next={fetchMoreData}
        hasMore={hasMore}
        loader={<div className="text-center py-4"><Spin tip="Đang tải thêm..." /></div>}
        className="flex flex-wrap gap-6 justify-center"
      >
        {newsItems.map((item) => (
          <div
            key={item.id}
            className="w-full max-w-xs cursor-pointer"
            onClick={() => handleCardClick(item.id)}
            ref={el => cardRefs.current[item.id] = el}
          >
            <NewsCard
              id={item.id}
              title={item.title}
              summary={item.summary}
              imageUrl={item.imageUrl}
              sourceUrl={item.sourceUrl}
              isSelected={item.id === selectedCardId}
            />
          </div>
        ))}
        {error && hasMore && (
          <div className="w-full text-red-500 text-center py-4">Lỗi khi tải thêm: {error}</div>
        )}
      </InfiniteScroll>

      {!hasMore && newsItems.length > 0 && (
        <div 
        className="fixed bottom-0 left-0 right-0 bg-gray-100 text-gray-600 text-center py-3"
        style={{
          textAlign: 'center',
          whiteSpace: 'normal',
          wordBreak: 'break-word'
        }}
        >
          <p>
            <b>Bạn đã cập nhật đến tin mới nhất, vui lòng tải lại trang</b>
          </p>
        </div>
      )}
    </div>
  );
};

export default NewsContent;
