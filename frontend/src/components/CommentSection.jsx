import React from 'react';
import { Input, Button, List, Typography, Avatar } from 'antd';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

const CommentSection = ({ comments = [], newComment, onNewCommentChange, onSubmitComment }) => {
  return (
    <div>
        {/* Phần hiển thị comment */}
        <List
        header={<Text strong>{`${comments.length} bình luận`}</Text>}
        itemLayout="horizontal"
        dataSource={comments}
        locale={{ emptyText: 'Chưa có bình luận nào' }}
        renderItem={item => (
            <List.Item>
            <List.Item.Meta
                avatar={<Avatar src={item.avatar || 'https://zos.alipayobjects.com/rmsportal/ODTLcjxAfvqbxHnVXCYX.png'} />} // Avatar mặc định
                title={<Text strong>{item.author || 'Ẩn danh'}</Text>}
                description={<Paragraph>{item.content}</Paragraph>}
            />
            </List.Item>
        )}
        />
      {/* Phần nhập comment */}
      <TextArea
        rows={3}
        placeholder="Viết bình luận của bạn..."
        value={newComment}
        onChange={onNewCommentChange}
        style={{ marginBottom: '10px' }}
      />
      <Button 
        type="primary" 
        onClick={onSubmitComment} 
        disabled={!newComment?.trim()} // Disable nếu input trống
        style={{ marginBottom: '20px' }}
      >
        Gửi bình luận
      </Button>
    </div>
  );
};

export default CommentSection; 