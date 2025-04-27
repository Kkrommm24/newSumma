import React, { useState, useEffect } from 'react';
import { Card, Drawer, Typography, App } from 'antd';
import { simpleActionIconsConfig } from "./InteractiveButtons";
import RatingComponent from "./RatingComponent";
import CommentSection from './CommentSection';
import axiosInstance from '../services/axiosInstance';
import { BookOutlined, BookFilled } from '@ant-design/icons';

const { Meta } = Card;
const { Text } = Typography;

const formatDate = (dateString) => {
  if (!dateString) return null;
  try {
    const date = new Date(dateString);
    const formatted = date.toLocaleString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
    return formatted;
  } catch (error) {
    console.error("Error formatting date:", error);
    return dateString;
  }
};

const NewsCard = ({ 
  id,
  articleId,
  title, 
  summary, 
  imageUrl, 
  sourceUrl, 
  publishedAt, 
  userVote, 
  upvotes: initialUpvotes, 
  downvotes: initialDownvotes, 
  isBookmarked,
  onBookmarkToggle,
  showBookmarkButton = true
}) => {
  const { message: messageApi } = App.useApp();
  const [isCommentDrawerVisible, setIsCommentDrawerVisible] = useState(false);
  const [displayUpvotes, setDisplayUpvotes] = useState(initialUpvotes || 0);
  const [displayDownvotes, setDisplayDownvotes] = useState(initialDownvotes || 0);
  const [currentUserVote, setCurrentUserVote] = useState(userVote);
  const [comments, setComments] = useState([
    { author: 'Người dùng A', content: 'Bài viết rất hay!', avatar: 'https://zos.alipayobjects.com/rmsportal/ODTLcjxAfvqbxHnVXCYX.png' },
    { author: 'Người dùng B', content: 'Tóm tắt khá ổn.' },
  ]);
  const [newComment, setNewComment] = useState('');

  useEffect(() => {
    setDisplayUpvotes(initialUpvotes || 0);
    setDisplayDownvotes(initialDownvotes || 0);
    setCurrentUserVote(userVote);
  }, [initialUpvotes, initialDownvotes, userVote]);

  const showCommentDrawer = () => {
    setIsCommentDrawerVisible(true);
  };

  const handleCommentDrawerClose = () => {
    setIsCommentDrawerVisible(false);
    setNewComment('');
  };

  const handleNewCommentChange = (e) => {
    setNewComment(e.target.value);
  };

  const handleSubmitComment = () => {
    if (!newComment.trim()) return;
    
    const commentToAdd = {
      author: 'Bạn',
      content: newComment,
    };
    
    setComments([...comments, commentToAdd]);
    setNewComment('');
  };

  const handleFeedbackSubmit = async (newVote) => {
    if (!id) {
      messageApi.error("Lỗi: Không tìm thấy ID tóm tắt.");
      return;
    }

    const previousVote = currentUserVote;
    let optimisticUpvoteChange = 0;
    let optimisticDownvoteChange = 0;

    if (newVote === true) {
      if (previousVote === null) optimisticUpvoteChange = 1;
      else if (previousVote === false) { optimisticUpvoteChange = 1; optimisticDownvoteChange = -1; }
    } else if (newVote === false) {
      if (previousVote === null) optimisticDownvoteChange = 1;
      else if (previousVote === true) { optimisticUpvoteChange = -1; optimisticDownvoteChange = 1; }
    } else {
      if (previousVote === true) optimisticUpvoteChange = -1;
      else if (previousVote === false) optimisticDownvoteChange = -1;
    }
    
    const prevState = { 
        upvotes: displayUpvotes, 
        downvotes: displayDownvotes, 
        vote: currentUserVote 
    };

    setDisplayUpvotes(prev => Math.max(0, prev + optimisticUpvoteChange));
    setDisplayDownvotes(prev => Math.max(0, prev + optimisticDownvoteChange));
    setCurrentUserVote(newVote);

    try {
      const payload = { summary_id: id };
      if (newVote !== null) {
        payload.is_upvote = newVote;
      }
      
      const response = await axiosInstance.post('/summarizer/summaries/feedback/', payload);

      if (response && response.data.status === 'success') {
        setDisplayUpvotes(response.data.upvotes);
        setDisplayDownvotes(response.data.downvotes);
        setCurrentUserVote(response.data.user_vote === true ? true : response.data.user_vote === false ? false : null);
      } else {
         messageApi.error(`Lỗi: ${response?.data?.message || 'Không thể gửi/xóa đánh giá.'}`);
         setDisplayUpvotes(prevState.upvotes);
         setDisplayDownvotes(prevState.downvotes);
         setCurrentUserVote(prevState.vote);
      }
    } catch (error) { 
      console.error('Error submitting/removing feedback:', error);
      messageApi.error('Đã xảy ra lỗi khi gửi/xóa đánh giá.');
      setDisplayUpvotes(prevState.upvotes);
      setDisplayDownvotes(prevState.downvotes);
      setCurrentUserVote(prevState.vote);
    }
  };

  const availableActionsConfig = [...simpleActionIconsConfig];

  const cardActions = [];

  if (showBookmarkButton && onBookmarkToggle) {
    const BookmarkIcon = isBookmarked ? BookFilled : BookOutlined;
    cardActions.push(
      <BookmarkIcon 
        key="bookmark" 
        onClick={(e) => { 
          e.stopPropagation();
          onBookmarkToggle(articleId, isBookmarked); 
        }} 
        style={{ color: isBookmarked ? '#111827' : undefined }}
      />
    );
  }

  const commentActionConfig = availableActionsConfig.find(a => a.key === 'comment');
  if (commentActionConfig) {
    cardActions.push(
      <commentActionConfig.IconComponent 
        key="comment" 
        onClick={(e) => {
          e.stopPropagation();
          showCommentDrawer();
        }} 
      />
    );
  }


  const shareActionConfig = availableActionsConfig.find(a => a.key === 'share');
  if (shareActionConfig) {
    cardActions.push(
      <shareActionConfig.IconComponent 
        key="share" 
        onClick={(e) => {
          e.stopPropagation();
          // Thêm logic share nếu cần
        }} 
      />
    );
  }

  return (
    <>
      <Card
        hoverable
        className="p-2 text-sm shadow-md overflow-hidden bg-white"
        cover={imageUrl ? <img alt={title} src={imageUrl} className="h-24 w-full object-cover" /> : null}
        size='small'
        style={{
          marginBottom: '3vh',
          marginTop: '3vh',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          transition: 'transform 0.2s',
          width: '100%'
        }}
        actions={cardActions}
      >
        <div className="flex justify-between items-start mt-1">
          <div className="flex-grow mr-2">
            <Meta
              title={
                <h3
                  className="text-lg font-semibold text-gray-800 text-center whitespace-normal break-words"
                  style={{
                    textAlign: 'center',
                    whiteSpace: 'normal',
                    wordBreak: 'break-word'
                  }}
                >
                  {title || 'Untitled'}
                </h3>
              }
              description={
                <p className="text-gray-600 text-xs mt-1 line-clamp-3">
                  {summary || 'No summary available.'}
                </p>
              }
            />
            {publishedAt && (
              <div className="mt-1 text-left" style={{ textAlign: 'left' }}>
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  Đăng lúc: {formatDate(publishedAt)}
                </Text>
              </div>
            )}
            {sourceUrl && sourceUrl !== '#' && (
              <div className="mt-2 text-right" style={{ textAlign: 'right' }}>
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 hover:underline text-xs font-medium"
                >
                  Đọc bài gốc
                </a>
              </div>
            )}
          </div>
          <div className="flex-shrink-0">
            <RatingComponent 
              onSubmitFeedback={handleFeedbackSubmit} 
              initialVote={currentUserVote}
              upvotes={displayUpvotes} 
              downvotes={displayDownvotes} 
            />
          </div>
        </div>
      </Card>

      <Drawer
        title={`Bình luận cho: ${title || 'Bài viết'}`}
        placement="right"
        onClose={handleCommentDrawerClose}
        open={isCommentDrawerVisible}
        width={450}
        destroyOnClose
      >
        <CommentSection 
          comments={comments}
          newComment={newComment}
          onNewCommentChange={handleNewCommentChange}
          onSubmitComment={handleSubmitComment}
        />
      </Drawer>
    </>
  );
};

export default NewsCard;

