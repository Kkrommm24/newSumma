"use client"

import { useState, useEffect } from "react"
import { Button, Typography } from "antd"
import { LikeOutlined, DislikeOutlined } from "@ant-design/icons"

const { Text } = Typography;

const RatingComponent = ({ onSubmitFeedback, initialVote, upvotes, downvotes }) => {
  const [liked, setLiked] = useState(initialVote)

  useEffect(() => {
    setLiked(initialVote);
  }, [initialVote]);

  const handleRate = (value) => {
    const newValue = liked === value ? null : value;
    
    if (onSubmitFeedback) {
      onSubmitFeedback(newValue);
    }
  }

  // Tạo component icon riêng lẻ để dễ đọc hơn
  const likeIcon = <LikeOutlined className="text-xl" />;
  const dislikeIcon = <DislikeOutlined className="text-xl" />;

  return (
    <div className="flex flex-col items-center space-y-1 p-1">
      <div className="flex items-center space-x-1">
        <Text type="secondary" className="mr-2 text-sm">Bạn thấy tóm tắt này thế 
        nào?</Text>
        <Button
          type={liked === true ? "primary" : "text"}
          icon={liked === true ? likeIcon : <Text type="secondary">{likeIcon}</Text>}
          onClick={() => handleRate(true)}
          size="small"
        />
        <Text type="secondary" style={{ fontSize: '11px', minWidth: '15px', textAlign:'center' }}>{upvotes ?? 0}</Text>
        <Button
          type={liked === false ? "primary" : "text"}
          danger={liked === false}
          icon={liked === false ? dislikeIcon : <Text type="secondary">{dislikeIcon}</Text>}
          onClick={() => handleRate(false)}
          size="small"
        />
        <Text type="secondary" style={{ fontSize: '11px', minWidth: '15px', textAlign:'center' }}>{downvotes ?? 0}</Text>
      </div>
    </div>
  )
}

export default RatingComponent

