import React, { useState, useEffect } from 'react';
import { Input, Button, List, Typography, Avatar, Space, Modal, App, Dropdown, Menu } from 'antd';
import { EditOutlined, DeleteOutlined, EllipsisOutlined } from '@ant-design/icons';
import axiosInstance from '../services/axiosInstance';
import { useAuth } from '../context/AuthContext.jsx';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

const CommentSection = ({ 
  comments = [], 
  newComment, 
  onNewCommentChange, 
  onSubmitComment, 
  isSubmitting, 
  fetchComments
}) => {
  const { message: messageApi, modal: modalApi } = App.useApp();
  const { isAuthenticated } = useAuth();
  const [localCurrentUserId, setLocalCurrentUserId] = useState(null);

  const [editingComment, setEditingComment] = useState(null);
  const [editedContent, setEditedContent] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      const storedUserInfo = localStorage.getItem('userInfo');
      if (storedUserInfo) {
        try {
          const parsedUser = JSON.parse(storedUserInfo);
          setLocalCurrentUserId(parsedUser?.id || null);
        } catch (e) {
          console.error("[CommentSection] useEffect - Error parsing userInfo:", e);
          setLocalCurrentUserId(null);
        }
      } else {
        setLocalCurrentUserId(null);
      }
    } else {
      setLocalCurrentUserId(null);
    }
  }, [isAuthenticated]);

  const handleEdit = (comment) => {
    setEditingComment(comment);
    setEditedContent(comment.content);
  };

  const handleCancelEdit = () => {
    setEditingComment(null);
    setEditedContent('');
  };

  const handleSaveEdit = async () => {
    if (!editingComment || !editedContent.trim()) return;
    try {
      await axiosInstance.patch(`/news/comments/${editingComment.id}/`, { content: editedContent });
      messageApi.success('Bình luận đã được cập nhật.');
      setEditingComment(null);
      setEditedContent('');
      if (fetchComments) fetchComments();
    } catch (error) {
      console.error("Error updating comment:", error);
      messageApi.error('Không thể cập nhật bình luận.');
    }
  };

  const handleDelete = (commentId) => {
    modalApi.confirm({
      title: 'Xác nhận xóa bình luận',
      content: 'Bạn có chắc chắn muốn xóa bình luận này không? Hành động này không thể hoàn tác.',
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      async onOk() {
        try {
          await axiosInstance.delete(`/news/comments/${commentId}/`);
          messageApi.success('Bình luận đã được xóa.');
          if (fetchComments) fetchComments();
        } catch (error) {
          console.error("Error deleting comment:", error);
          messageApi.error('Không thể xóa bình luận.');
        }
      },
    });
  };

  return (
    <div>
        <List
        header={<Text strong>{`${comments.length} bình luận`}</Text>}
        itemLayout="horizontal"
        dataSource={comments}
        locale={{ emptyText: 'Chưa có bình luận nào' }}
        renderItem={item => {
            const menuItems = [
                {
                    key: 'edit',
                    icon: <EditOutlined />,
                    label: 'Sửa',
                    onClick: () => handleEdit(item),
                },
                {
                    key: 'delete',
                    icon: <DeleteOutlined />,
                    label: 'Xóa',
                    danger: true,
                    onClick: () => handleDelete(item.id),
                }
            ];

            return (
                <List.Item
                actions={localCurrentUserId && item.user && item.user.id === localCurrentUserId ? [
                    <Dropdown menu={{ items: menuItems }} trigger={['click']} key={`actions-${item.id}`}>
                        <Button type="text" icon={<EllipsisOutlined />} />
                    </Dropdown>
                ] : []}
                >
                {editingComment && editingComment.id === item.id ? (
                    <div style={{ width: '100%' }}>
                        <TextArea 
                            rows={2} 
                            value={editedContent} 
                            onChange={(e) => setEditedContent(e.target.value)} 
                        />
                        <Space style={{ marginTop: '8px' }}>
                            <Button type="primary" size="small" onClick={handleSaveEdit}>Lưu</Button>
                            <Button size="small" onClick={handleCancelEdit}>Hủy</Button>
                        </Space>
                    </div>
                ) : (
                    <List.Item.Meta
                        avatar={<Avatar src={item.user?.avatar || 'https://zos.alipayobjects.com/rmsportal/ODTLcjxAfvqbxHnVXCYX.png'} />}
                        title={<Text strong>{item.user?.username || 'Ẩn danh'}</Text>}
                        description={<Paragraph style={{ whiteSpace: 'pre-line' }}>{item.content}</Paragraph>}
                    />
                )}
                </List.Item>
            );
        }}
        />
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
        disabled={!newComment?.trim() || isSubmitting}
        loading={isSubmitting}
        style={{ marginBottom: '20px' }}
      >
        Gửi bình luận
      </Button>
    </div>
  );
};

export default CommentSection; 