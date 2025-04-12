import React, { useState } from 'react';
import { Card, Drawer } from 'antd';
import { simpleActionIconsConfig } from "./InteractiveButtons";
import RatingComponent from "./RatingComponent";
import CommentSection from './CommentSection';

const { Meta } = Card;

const NewsCard = ({ id, title, summary, imageUrl, sourceUrl }) => {
  const [isCommentDrawerVisible, setIsCommentDrawerVisible] = useState(false);
  const [comments, setComments] = useState([
    { author: 'Người dùng A', content: 'Bài viết rất hay!', avatar: 'https://zos.alipayobjects.com/rmsportal/ODTLcjxAfvqbxHnVXCYX.png' },
    { author: 'Người dùng B', content: 'Tóm tắt khá ổn.' },
  ]);
  const [newComment, setNewComment] = useState('');

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

  const cardActions = simpleActionIconsConfig.map(action => {
    const { key, IconComponent } = action;
    let onClickHandler = () => console.log(`${key} clicked!`);

    if (key === 'comment') {
      onClickHandler = showCommentDrawer;
    } else if (key === 'bookmark') {
      // onClickHandler = handleBookmark;
    } else if (key === 'share') {
      // onClickHandler = handleShare;
    }

    return <IconComponent key={key} onClick={onClickHandler} />;
  });

  return (
    <>
      <Card
        hoverable
        className="p-2 text-sm shadow-md overflow-hidden bg-white"
        cover={imageUrl ? <img alt={title} src={imageUrl} className="h-24 w-full object-cover" /> : null}
        size='small'
        style={{
          marginBottom: '30px',
          marginTop: '30px',
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
            <RatingComponent />
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

