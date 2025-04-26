import React, { useState, useEffect, useRef, useCallback } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Spin } from 'antd';
import NewsCard from "./NewsCard";
import { useSelector, useDispatch } from 'react-redux';
import { fetchNews } from '../store/slices/newsSlice';

const NEWS_PER_PAGE = 10;

const getRequestKey = (mode, query) => {
  return query ? `search:${query}` : mode;
};

const NewsContent = ({ fetchMode = 'recommendations', searchQuery = null }) => {
  const dispatch = useDispatch();
  const [selectedCardId, setSelectedCardId] = useState(null);
  const cardRefs = useRef({});
  
  const requestKey = getRequestKey(fetchMode, searchQuery);

  const { 
      items = [], 
      status = 'idle', 
      error = null, 
      currentPageToLoad = 1,
      hasMore = true
  } = useSelector((state) => state.news.requests[requestKey] || {}); 

  const isLoading = status === 'loading';
  const isInitialLoading = isLoading && items.length === 0;

  useEffect(() => {
    if (status === 'idle') {
      console.log(`NewsContent: Dispatching fetchNews for key: ${requestKey}, page: 1`);
      dispatch(fetchNews({ mode: fetchMode, query: searchQuery, page: 1 }));
    }
    // Nếu bạn muốn reset state khi component unmount hoặc mode/query thay đổi:
    // return () => { dispatch(resetNewsState({ mode: fetchMode, query: searchQuery })); }
    
  }, [dispatch, fetchMode, searchQuery, requestKey, status]);

  useEffect(() => {
    if (selectedCardId && cardRefs.current[selectedCardId]) {
        cardRefs.current[selectedCardId].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
  }, [selectedCardId]);

  const fetchMoreData = useCallback(() => {
    if (!isLoading && hasMore) {
      console.log(`NewsContent: Dispatching fetchNews for key: ${requestKey}, page: ${currentPageToLoad}`);
      dispatch(fetchNews({ mode: fetchMode, query: searchQuery, page: currentPageToLoad }));
    }
  }, [dispatch, fetchMode, searchQuery, requestKey, isLoading, hasMore, currentPageToLoad]);

  const handleCardClick = (id) => {
    setSelectedCardId(id);
  };

  if (isInitialLoading) {
    return <div className="text-center py-10"><Spin size="large" /></div>;
  }

  if (status === 'failed' && items.length === 0) {
    return <div className="text-red-600 bg-red-100 p-4 rounded text-center">Lỗi tải dữ liệu: {error || 'Unknown error'}</div>;
  }

  if (status !== 'loading' && items.length === 0) {
    const message = searchQuery 
       ? `Không tìm thấy kết quả nào cho "${searchQuery}".` 
       : "Không có tin tức nào để hiển thị.";
    return <div className="text-center py-10 text-gray-500">{message}</div>;
  }

  return (
    <div className="relative min-h-screen">
      <InfiniteScroll
        dataLength={items.length}
        next={fetchMoreData}
        hasMore={hasMore}
        loader={<div className="text-center py-4"><Spin tip="Đang tải thêm..." /></div>}
        className="flex flex-wrap gap-6 justify-center"
      >
        {items.map((item) => (
          <div
            key={`${item.id}-${requestKey}`}
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
              publishedAt={item.publishedAt}
              isSelected={item.id === selectedCardId}
              userVote={item.userVote}
              upvotes={item.upvotes}
              downvotes={item.downvotes}
            />
          </div>
        ))}
        {status === 'failed' && hasMore && (
          <div className="w-full text-red-500 text-center py-4">Lỗi khi tải thêm: {error || 'Unknown error'}</div>
        )}
      </InfiniteScroll>

      {!hasMore && items.length > 0 && (
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
