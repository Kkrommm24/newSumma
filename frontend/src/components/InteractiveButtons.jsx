"use client"
import { BookOutlined, ShareAltOutlined, CommentOutlined, StarOutlined } from "@ant-design/icons";
import React from 'react';

// Thay đổi: Export mảng cấu hình thay vì element
export const simpleActionIconsConfig = [
  { key: 'bookmark', IconComponent: BookOutlined },
  { key: 'comment', IconComponent: CommentOutlined },
  { key: 'share', IconComponent: ShareAltOutlined }
];

// Giữ nguyên RatingModalTrigger nếu bạn vẫn muốn dùng nó ở đâu đó
// Hoặc xóa đi nếu không cần nữa.
// Chúng ta sẽ không dùng nó trong NewsCard nữa.
// export const RatingModalTrigger = ({ onClick }) => (
//   <StarOutlined key="rate-trigger" onClick={onClick} />
// );

// Xóa export RatingModalTrigger nếu không dùng
// ...
