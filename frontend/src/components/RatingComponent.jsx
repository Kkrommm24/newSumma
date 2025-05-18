"use client"

import { useState, useEffect } from "react"
import { Button, Typography } from "antd"
import { LikeOutlined, DislikeOutlined } from "@ant-design/icons"
import { useDispatch } from "react-redux"
import { submitFeedback } from "../store/slices/newsSlice"

const { Text } = Typography;

const RatingComponent = ({ onSubmitFeedback, initialVote, upvotes, downvotes, summaryId }) => {
  const dispatch = useDispatch();
  const [liked, setLiked] = useState(initialVote);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localUpvotes, setLocalUpvotes] = useState(upvotes);
  const [localDownvotes, setLocalDownvotes] = useState(downvotes);

  // Cập nhật state khi props thay đổi
  useEffect(() => {
    setLiked(initialVote);
    setLocalUpvotes(upvotes);
    setLocalDownvotes(downvotes);
  }, [initialVote, upvotes, downvotes]);

  const handleRate = async (value) => {
    if (isSubmitting || !summaryId) return;
    
    const newValue = liked === value ? null : value;
    setIsSubmitting(true);
    
    try {
      const result = await dispatch(submitFeedback({ 
        summaryId, 
        isUpvote: newValue 
      })).unwrap();
      
      if (result.status === 'success') {
        // Cập nhật UI sau khi API call thành công
        if (newValue === true) {
          setLocalUpvotes(prev => prev + 1);
          if (liked === false) setLocalDownvotes(prev => prev - 1);
        } else if (newValue === false) {
          setLocalDownvotes(prev => prev + 1);
          if (liked === true) setLocalUpvotes(prev => prev - 1);
        } else {
          if (liked === true) setLocalUpvotes(prev => prev - 1);
          if (liked === false) setLocalDownvotes(prev => prev - 1);
        }
        setLiked(newValue);
    
    if (onSubmitFeedback) {
      onSubmitFeedback(newValue);
    }
      } else {
        console.error('Error submitting feedback:', result.message);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Tạo component icon riêng lẻ để dễ đọc hơn
  const likeIcon = <LikeOutlined className="text-xl" />;
  const dislikeIcon = <DislikeOutlined className="text-xl" />;

  return (
    <div className="flex flex-col items-center space-y-1 p-1">
      <div className="flex items-center space-x-1">
        <Text type="secondary" className="mr-2 text-sm">Bạn có thấy tóm tắt bài viết này chính xác không?</Text>
        <Button
          type={liked === true ? "primary" : "text"}
          icon={liked === true ? likeIcon : <Text type="secondary">{likeIcon}</Text>}
          onClick={() => handleRate(true)}
          size="small"
          loading={isSubmitting}
        />
        <Text type="secondary" style={{ fontSize: '11px', minWidth: '15px', textAlign:'center' }}>{localUpvotes ?? 0}</Text>
        <Button
          type={liked === false ? "primary" : "text"}
          danger={liked === false}
          icon={liked === false ? dislikeIcon : <Text type="secondary">{dislikeIcon}</Text>}
          onClick={() => handleRate(false)}
          size="small"
          loading={isSubmitting}
        />
        <Text type="secondary" style={{ fontSize: '11px', minWidth: '15px', textAlign:'center' }}>{localDownvotes ?? 0}</Text>
      </div>
    </div>
  );
};

export default RatingComponent

