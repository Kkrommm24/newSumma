import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Spin, App, Button } from 'antd';
import NewsCard from "./NewsCard";
import { useSelector, useDispatch } from 'react-redux';
import { createSelector } from '@reduxjs/toolkit';
import { fetchNews, submitFeedback } from '../store/slices/newsSlice';
import { addBookmark, removeBookmark, fetchBookmarks } from '../store/slices/userSlice';
import { useAuth } from '../context/AuthContext.jsx';
import axiosInstance from '../services/axiosInstance';

const NEWS_PER_PAGE = 10;

const getRequestKey = (mode, query) => {
  return query ? `search:${query}` : mode;
};

// Tạo các selectors riêng biệt cho từng phần của state
const selectNewsItems = createSelector(
  [(state) => state.news.requests, (_, requestKey) => requestKey],
  (requests, requestKey) => {
    const items = requests[requestKey]?.items;
    return Array.isArray(items) ? items : [];
  }
);

const selectNewsStatus = createSelector(
  [(state) => state.news.requests, (_, requestKey) => requestKey],
  (requests, requestKey) => {
    const status = requests[requestKey]?.status;
    return typeof status === 'string' ? status : 'idle';
  }
);

const selectNewsError = createSelector(
  [(state) => state.news.requests, (_, requestKey) => requestKey],
  (requests, requestKey) => {
    const error = requests[requestKey]?.error;
    return error || null;
  }
);

const selectCurrentPage = createSelector(
  [(state) => state.news.requests, (_, requestKey) => requestKey],
  (requests, requestKey) => {
    const page = requests[requestKey]?.currentPage;
    return typeof page === 'number' ? page : 1;
  }
);

const selectHasMore = createSelector(
  [(state) => state.news.requests, (_, requestKey) => requestKey],
  (requests, requestKey) => {
    const hasMore = requests[requestKey]?.hasMore;
    return typeof hasMore === 'boolean' ? hasMore : true;
  }
);

const selectBookmarks = createSelector(
  [(state) => state.user?.bookmarks?.items],
  (items) => {
    return Array.isArray(items) ? items : [];
  }
);

const selectBookmarksStatus = createSelector(
  [(state) => state.user?.bookmarks?.status],
  (status) => {
    return typeof status === 'string' ? status : 'idle';
  }
);

const selectDownvotedArticles = createSelector(
  [(state) => state.user?.downvotes?.items],
  (items) => {
    return Array.isArray(items) ? items : [];
  }
);

const selectPendingDownvotes = createSelector(
  [(state) => state.user?.downvotes?.pending],
  (items) => {
    return Array.isArray(items) ? items : [];
  }
);

const selectVotes = createSelector(
  [(state) => state.user?.votes?.items],
  (items) => {
    return Array.isArray(items) ? items : [];
  }
);

const NewsContent = ({ fetchMode = 'recommendations', searchQuery = null }) => {
  const dispatch = useDispatch();
  const { message: messageApi, notification } = App.useApp();
  const [selectedCardId, setSelectedCardId] = useState(null);
  const cardRefs = useRef({});
  const { isAuthenticated } = useAuth();
  
  const requestKey = useMemo(() => getRequestKey(fetchMode, searchQuery), [fetchMode, searchQuery]);
  const isFetching = useRef(false); 
  const visibleCardTimers = useRef(new Map());
  const deliberatelySelectedForScroll = useRef(false);

  const userVotes = useSelector(state => state.news.userVotes);

  const hiddenArticles = useMemo(() => {
    return new Set(Object.entries(userVotes || {})
      .filter(([_, vote]) => vote === false)
      .map(([id]) => id));
  }, [userVotes]);

  const [lastHiddenByDownvote, setLastHiddenByDownvote] = useState(null);
  const [togglingBookmarkArticleId, setTogglingBookmarkArticleId] = useState(null);

  const newsItems = useSelector(state => selectNewsItems(state, requestKey));
  const newsStatus = useSelector(state => selectNewsStatus(state, requestKey));
  const newsError = useSelector(state => selectNewsError(state, requestKey));
  const currentPage = useSelector(state => selectCurrentPage(state, requestKey));
  const hasMore = useSelector(state => selectHasMore(state, requestKey));
  const bookmarks = useSelector(selectBookmarks);
  const bookmarksStatus = useSelector(selectBookmarksStatus);

  const bookmarkedArticleIds = useMemo(() => {
    const ids = new Set(bookmarks.map(b => b.article?.id).filter(id => id != null));
    return ids;
  }, [bookmarks]);

  const isInitialLoading = newsStatus === 'loading' && newsItems.length === 0;

  useEffect(() => {
    isFetching.current = (newsStatus === 'loading');
  }, [newsStatus]);

  useEffect(() => {
    if (isAuthenticated && bookmarksStatus === 'idle') {
      dispatch(fetchBookmarks());
    }
  }, [dispatch, isAuthenticated, bookmarksStatus]);

  useEffect(() => {
    if (newsStatus === 'idle') {
      dispatch(fetchNews({ mode: fetchMode, query: searchQuery, page: 1 }));
    }
  }, [dispatch, fetchMode, searchQuery, requestKey, newsStatus]);

  useEffect(() => {
    if (selectedCardId && cardRefs.current[selectedCardId] && deliberatelySelectedForScroll.current) {
        cardRefs.current[selectedCardId].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
        deliberatelySelectedForScroll.current = false; 
    }
  }, [selectedCardId]);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') {
      console.warn("IntersectionObserver is not supported in this browser.");
      return;
    }

    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.75,
    };

    const sendViewTime = async (summaryId, durationSeconds) => {
      if (!summaryId || durationSeconds <= 3) {
        return;
      }

      try {
        await axiosInstance.post('/recommender/log-view-time/', {
          summary_id: summaryId,
          duration_seconds: durationSeconds
        });
      } catch (error) {
        console.error('Error logging view time:', error);
      }
    };

    const intersectionCallback = (entries) => {
      entries.forEach((entry) => {
        const summaryId = entry.target.dataset.summaryId;
        if (!summaryId) {
          return;
        }

        if (entry.isIntersecting) {
          if (!visibleCardTimers.current.has(summaryId)) {
            visibleCardTimers.current.set(summaryId, Date.now());
          }
        } else {
          if (visibleCardTimers.current.has(summaryId)) {
            const startTime = visibleCardTimers.current.get(summaryId);
            const timeSpentSeconds = (Date.now() - startTime) / 1000;
            sendViewTime(summaryId, timeSpentSeconds);
            visibleCardTimers.current.delete(summaryId);
          }
        }
      });
    };

    const observer = new IntersectionObserver(intersectionCallback, observerOptions);

    const currentCardElements = Object.values(cardRefs.current).filter(el => el instanceof HTMLElement);
    currentCardElements.forEach(cardElement => observer.observe(cardElement));

    const handleVisibilityChange = () => {
      if (document.hidden) {
        visibleCardTimers.current.forEach((startTime, summaryId) => {
          const timeSpentSeconds = (Date.now() - startTime) / 1000;
          sendViewTime(summaryId, timeSpentSeconds);
        });
        visibleCardTimers.current.clear();
      } else {
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      currentCardElements.forEach(cardElement => {
        if (observer && cardElement) observer.unobserve(cardElement);
      });
      
      visibleCardTimers.current.forEach((startTime, summaryId) => {
        const timeSpentSeconds = (Date.now() - startTime) / 1000;
        sendViewTime(summaryId, timeSpentSeconds);
      });
      visibleCardTimers.current.clear();
      
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (observer) observer.disconnect();
    };
  }, [newsItems, isAuthenticated]);

  const fetchMoreNews = useCallback(async () => {
    if (isFetching.current || !hasMore) return;
    
    isFetching.current = true;
    try {
      dispatch(fetchNews({ 
        mode: fetchMode, 
        query: searchQuery, 
        page: currentPage + 1 
      }));
    } catch (error) {
      console.error('Error fetching more news:', error);
    } finally {
      isFetching.current = false;
    }
  }, [dispatch, fetchMode, searchQuery, currentPage, hasMore]);

  const handleCardClick = (id) => {
    if (selectedCardId !== id) {
        setSelectedCardId(id);
        deliberatelySelectedForScroll.current = true;
    } else {
        deliberatelySelectedForScroll.current = false; 
    }
  };

  const handleBookmarkToggle = useCallback(async (articleIdFromCard, isCurrentlyBookmarked) => {
    if (!isAuthenticated) {
        messageApi.warning('Vui lòng đăng nhập để sử dụng chức năng này.');
        return;
    }
    if (!articleIdFromCard) {
        messageApi.error('Lỗi: Không tìm thấy ID bài viết.');
        return;
    }
    if (togglingBookmarkArticleId === articleIdFromCard) {
        return;
    }

    setTogglingBookmarkArticleId(articleIdFromCard);

    const action = isCurrentlyBookmarked ? removeBookmark(articleIdFromCard) : addBookmark(articleIdFromCard);
    const successMessage = isCurrentlyBookmarked ? 'Đã xóa khỏi bookmark.' : 'Đã lưu vào bookmark.';
    const failureMessage = isCurrentlyBookmarked ? 'Lỗi khi xóa bookmark.' : 'Lỗi khi lưu bookmark.';

    try {
        await dispatch(action).unwrap();
        messageApi.success(successMessage);
    } catch (error) {
        console.error("Bookmark toggle error:", error);
        messageApi.error(error?.message || failureMessage);
    } finally {
        setTogglingBookmarkArticleId(null);
    }
  }, [dispatch, isAuthenticated, messageApi, togglingBookmarkArticleId]);

  // Hàm callback này sẽ được gọi từ NewsCard khi downvote thành công
  const handleSuccessfulDownvote = useCallback((summaryId) => {
    setLastHiddenByDownvote(summaryId);
  }, []); // Không có dependencies, sẽ không bị tạo lại trừ khi component unmount

  useEffect(() => {
    if (lastHiddenByDownvote) {
      const summaryIdToUndo = lastHiddenByDownvote; 
      
      const hiddenItem = newsItems.find(item => item.id === summaryIdToUndo);
      const messageText = hiddenItem 
        ? `Bài viết đã bị tạm ẩn vì bạn cho rằng phần tóm tắt không chính xác. Chúng tôi sẽ xem xét và cập nhật sớm nhất có thể.`
        : "Bài viết đã bị tạm ẩn vì bạn cho rằng phần tóm tắt không chính xác. Chúng tôi sẽ xem xét và cập nhật sớm nhất có thể.";

      const key = `undo-downvote-${summaryIdToUndo}`;
      
      notification.info({
        message: messageText,
        description: (
            <Button 
                type="primary"
                size="small"
                className="custom-undo-button"
                onClick={() => {
                    handleUndoDownvote(summaryIdToUndo);
                    notification.destroy(key);
                }}
            >
                Hoàn tác
            </Button>
        ),
        key: key,
        duration: 7,
        onClose: () => {
        }
      });
      setLastHiddenByDownvote(null); 
    }
  }, [lastHiddenByDownvote, notification, newsItems, dispatch]); // Thêm dispatch vì handleUndoDownvote dùng

  const handleUndoDownvote = useCallback(async (summaryId) => {
    if (!summaryId) return;
    try {
      const result = await dispatch(submitFeedback({ 
        summaryId, 
        isUpvote: null
      })).unwrap();

      if (result.status === 'success') {
        messageApi.success('Đã hoàn tác đánh giá không tốt cho tóm tắt của bài viết.');
      } else {
        messageApi.error(result.message || 'Không thể hoàn tác. Vui lòng thử lại.');
      }
    } catch (error) {
      const errorMessage = error?.payload || error?.message || 'Lỗi khi hoàn tác. Vui lòng thử lại.';
      console.error('Error undoing downvote:', error);
      messageApi.error(errorMessage);
    }
  }, [dispatch, messageApi]); // Chỉ phụ thuộc dispatch và messageApi

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
        next={fetchMoreNews}
        hasMore={hasMore}
        loader={<div className="text-center py-4"><Spin /></div>}
        className="flex flex-wrap gap-6 justify-center"
        scrollThreshold="200px"
        scrollableTarget="scrollableDiv"
      >
        {newsItems
          .filter(item => !hiddenArticles.has(item.id))
          .map((item) => {
          const isBookmarked = bookmarkedArticleIds.has(item.articleId);
          // userVote cho NewsCard nên lấy trực tiếp từ userVotes của newsSlice
          const userVoteForCard = userVotes[item.id] !== undefined ? userVotes[item.id] : item.userVote; 

          return (
            <div
              key={`${item.id}-${requestKey}`}
              className="w-full max-w-xs cursor-pointer"
              onClick={() => handleCardClick(item.id)}
              ref={el => cardRefs.current[item.id] = el}
              data-summary-id={item.id}
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
                userVote={userVoteForCard}
                upvotes={item.upvotes}
                downvotes={item.downvotes}
                commentCount={item.comment_count}
                isBookmarked={isBookmarked}
                onBookmarkToggle={handleBookmarkToggle}
                showBookmarkButton={isAuthenticated}
                isTogglingBookmark={togglingBookmarkArticleId === item.articleId}
                onSuccessfulDownvote={handleSuccessfulDownvote}
                category_name={item.category_name}
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
