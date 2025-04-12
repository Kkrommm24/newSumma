import React, { useState, useEffect, useRef, useCallback } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Spin } from 'antd';
import NewsCard from "./NewsCard";

const NewsContent = () => {
  const [newsItems, setNewsItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCardId, setSelectedCardId] = useState(null);
  const cardRefs = useRef({});
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchNews = useCallback(async (currentPage) => {
    if (currentPage === 1) {
      setLoading(true);
    }
    setError(null);
    try {
      const response = await fetch(`/api/summaries/?sort_by=-created_at&page=${currentPage}`);
      if (!response.ok) {
        const errorData = { status: response.status, message: response.statusText };
        try {
          errorData.body = await response.text();
        } catch (e) { /* Bỏ qua */ }
        throw new Error(JSON.stringify(errorData));
      }
      const data = await response.json();

      if (data && data.results) {
        const formattedData = data.results.map(item => ({
          id: item.id,
          title: item.title || 'Không có tiêu đề',
          summary: item.summary_text || 'Không có tóm tắt',
          imageUrl: item.image_url || null,
          sourceUrl: item.url || '#'
        }));

        setNewsItems(prevItems =>
          currentPage === 1 ? formattedData : [...prevItems, ...formattedData]
        );
        setHasMore(data.next !== null);
        setPage(currentPage);
      } else {
        setHasMore(false);
        if (currentPage === 1) setNewsItems([]);
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
      if (currentPage === 1) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchNews(1);
  }, [fetchNews]);

  useEffect(() => {
    if (selectedCardId && cardRefs.current[selectedCardId]) {
      cardRefs.current[selectedCardId].scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }, [selectedCardId]);

  const fetchMoreData = () => {
    if (!hasMore) return;
    fetchNews(page + 1);
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

      {/* Thông báo cố định ở cuối màn hình khi hết bài viết */}
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
