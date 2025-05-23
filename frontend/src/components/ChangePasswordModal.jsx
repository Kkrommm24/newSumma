import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Alert } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import axiosInstance from '../services/axiosInstance';

const ChangePasswordModal = ({ visible, onClose }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (values) => {
    if (values.new_password !== values.new_password_confirm) {
      setError('Mật khẩu xác nhận không khớp!');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await axiosInstance.post('/user/change-password/', {
        old_password: values.oldPassword,
        new_password: values.new_password,
        new_password_confirm: values.new_password_confirm,
      });
      message.success('Đổi mật khẩu thành công!');
      form.resetFields();
      onClose();
    } catch (error) {
      let errorMessage = 'Đổi mật khẩu thất bại. Vui lòng thử lại.';
      
      if (error.response?.data) {
        if (error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.old_password) {
          const oldPasswordError = error.response.data.old_password;
          errorMessage = Array.isArray(oldPasswordError) ? oldPasswordError[0].replace(/[\[\]']/g, '') : oldPasswordError;
        } else if (error.response.data.new_password) {
          const newPasswordError = error.response.data.new_password;
          errorMessage = Array.isArray(newPasswordError) ? newPasswordError[0].replace(/[\[\]']/g, '') : newPasswordError;
        } else if (error.response.data.new_password_confirm) {
          const confirmError = error.response.data.new_password_confirm;
          errorMessage = Array.isArray(confirmError) ? confirmError[0].replace(/[\[\]']/g, '') : confirmError;
        } else if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.error) {
          errorMessage = error.response.data.error;
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Đổi mật khẩu"
      open={visible}
      onCancel={onClose}
      footer={null}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        {error && (
          <Form.Item className="mb-5">
            <Alert 
              message={error} 
              type="error" 
              showIcon
              style={{
                backgroundColor: '#fff2f0',
                border: '1px solid #ffccc7',
                color: '#cf1322'
              }}
            />
          </Form.Item>
        )}

        <Form.Item
          name="oldPassword"
          label="Mật khẩu hiện tại"
          rules={[{ required: true, message: 'Vui lòng nhập mật khẩu hiện tại!' }]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Nhập mật khẩu hiện tại"
          />
        </Form.Item>

        <Form.Item
          name="new_password"
          label="Mật khẩu mới"
          rules={[
            { required: true, message: 'Vui lòng nhập mật khẩu mới!' },
            { min: 8, message: 'Mật khẩu phải có ít nhất 8 ký tự!' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Nhập mật khẩu mới"
          />
        </Form.Item>

        <Form.Item
          name="new_password_confirm"
          label="Xác nhận mật khẩu mới"
          dependencies={['new_password']}
          rules={[
            { required: true, message: 'Vui lòng xác nhận mật khẩu mới!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Mật khẩu xác nhận không khớp!'));
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Xác nhận mật khẩu mới"
          />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            className="w-full"
            style={{ backgroundColor: '#252525', borderColor: '#252525' }}
          >
            Đổi mật khẩu
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ChangePasswordModal; 
