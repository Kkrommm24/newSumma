import React, { useState, useEffect, useRef, useCallback } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Spin, App } from 'antd';
import NewsCard from "./NewsCard";
import { useSelector, useDispatch } from 'react-redux';
import { fetchNews } from '../store/slices/newsSlice';
import { addBookmark, removeBookmark, fetchBookmarks } from '../store/slices/userSlice';
import { useAuth } from '../context/AuthContext.jsx';

const NEWS_PER_PAGE = 10;

const getRequestKey = (mode, query) => {
  return query ? `search:${query}` : mode;
};

const NewsContent = ({ fetchMode = 'recommendations', searchQuery = null }) => {
  const dispatch = useDispatch();
  const { message: messageApi } = App.useApp();
  const [selectedCardId, setSelectedCardId] = useState(null);
  const cardRefs = useRef({});
  const { isAuthenticated } = useAuth();
  
  const requestKey = getRequestKey(fetchMode, searchQuery);

  const { 
      items: newsItems = [], 
      status: newsStatus = 'idle', 
      error: newsError = null, 
      currentPage = 1,
      hasMore = true
  } = useSelector((state) => state.news.requests[requestKey] || {}); 

  const { items: bookmarks = [], status: bookmarksStatus } = useSelector((state) => state.user.bookmarks);
  const bookmarkedArticleIds = React.useMemo(() => new Set(bookmarks.map(b => b.article?.id)), [bookmarks]);

  const isLoading = newsStatus === 'loading';
  const isInitialLoading = isLoading && newsItems.length === 0;

  useEffect(() => {
    if (isAuthenticated && bookmarksStatus === 'idle') {
      dispatch(fetchBookmarks());
    }
  }, [dispatch, isAuthenticated, bookmarksStatus]);

  useEffect(() => {
    if (newsStatus === 'idle') {
      dispatch(fetchNews({ mode: fetchMode, query: searchQuery, page: 1 }));
    }
    // Nếu bạn muốn reset state khi component unmount hoặc mode/query thay đổi:
    // return () => { dispatch(resetNewsState({ mode: fetchMode, query: searchQuery })); }
    
  }, [dispatch, fetchMode, searchQuery, requestKey, newsStatus]);

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
      dispatch(fetchNews({ mode: fetchMode, query: searchQuery, page: currentPage }));
    }
  }, [dispatch, fetchMode, searchQuery, requestKey, isLoading, hasMore, currentPage]);

  const handleCardClick = (id) => {
    setSelectedCardId(id);
  };

  const handleBookmarkToggle = useCallback(async (articleId, isCurrentlyBookmarked) => {
    if (!isAuthenticated) {
        messageApi.warning('Vui lòng đăng nhập để sử dụng chức năng này.');
        return;
    }
    if (!articleId) {
        messageApi.error('Lỗi: Không tìm thấy ID bài viết.');
        return;
    }

    const action = isCurrentlyBookmarked ? removeBookmark(articleId) : addBookmark(articleId);
    const successMessage = isCurrentlyBookmarked ? 'Đã xóa khỏi bookmark.' : 'Đã lưu vào bookmark.';
    const failureMessage = isCurrentlyBookmarked ? 'Lỗi khi xóa bookmark.' : 'Lỗi khi lưu bookmark.';

    try {
        await dispatch(action).unwrap();
        messageApi.success(successMessage);
    } catch (error) {
        console.error("Bookmark toggle error:", error);
        messageApi.error(error?.message || failureMessage);
    }
  }, [dispatch, isAuthenticated, messageApi]);

  if (isInitialLoading) {
    return <div className="text-center py-10"><Spin size="large" /></div>;
  }

  if (newsStatus === 'failed' && newsItems.length === 0) {
    return <div className="text-red-600 bg-red-100 p-4 rounded text-center">Lỗi tải dữ liệu: {newsError || 'Unknown error'}</div>;
  }

  if (newsStatus !== 'loading' && newsItems.length === 0) {
    const message = searchQuery 
       ? `Không tìm thấy kết quả nào cho "${searchQuery}".` 
       : "Không có tin tức nào để hiển thị.";
    return <div className="text-center py-10 text-gray-500">{message}</div>;
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
        {newsItems.map((item) => {
          const isBookmarked = bookmarkedArticleIds.has(item.articleId);

          return (
            <div
              key={`${item.id}-${requestKey}`}
              className="w-full max-w-xs cursor-pointer"
              onClick={() => handleCardClick(item.id)}
              ref={el => cardRefs.current[item.id] = el}
            >
              <NewsCard
                id={item.id}
                articleId={item.articleId}
                title={item.title}
                summary={item.summary}
                imageUrl={item.imageUrl}
                sourceUrl={item.sourceUrl}
                publishedAt={item.publishedAt}
                isSelected={item.id === selectedCardId}
                userVote={item.userVote}
                upvotes={item.upvotes}
                downvotes={item.downvotes}
                isBookmarked={isBookmarked}
                onBookmarkToggle={handleBookmarkToggle}
                showBookmarkButton={isAuthenticated}
              />
            </div>
          );
        })}
        {newsStatus === 'failed' && hasMore && (
          <div className="w-full text-red-500 text-center py-4">Lỗi khi tải thêm: {newsError || 'Unknown error'}</div>
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
