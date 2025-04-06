"use client"

import { useState } from "react"
import { Button, Typography } from "antd"
import { LikeOutlined, DislikeOutlined } from "@ant-design/icons"

const { Text } = Typography;

const RatingComponent = ({ onRated }) => {
  const [liked, setLiked] = useState(null)

  const handleRate = (value) => {
    const newValue = liked === value ? null : value;
    setLiked(newValue)
    if (onRated) {
      onRated(newValue)
    }
  }

  // Tạo component icon riêng lẻ để dễ đọc hơn
  const likeIcon = <LikeOutlined className="text-xl" />;
  const dislikeIcon = <DislikeOutlined className="text-xl" />;

  return (
    <div className="flex items-center justify-center space-x-2 p-2">
      <Text type="secondary" className="mr-2 text-sm">Bạn thấy tóm tắt này thế nào?</Text>
      <Button
        type={liked === true ? "primary" : "text"}
        icon={liked === true ? likeIcon : <Text type="secondary">{likeIcon}</Text>}
        onClick={() => handleRate(true)}
        size="middle"
        style={{marginLeft: '5px' }}
      />
      <Button
        type={liked === false ? "primary" : "text"}
        danger={liked === false}
        icon={liked === false ? dislikeIcon : <Text type="secondary">{dislikeIcon}</Text>}
        onClick={() => handleRate(false)}
        size="middle"
      />
    </div>
  )
}

export default RatingComponent

