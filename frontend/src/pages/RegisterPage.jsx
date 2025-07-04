import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Typography, Spin, Alert, Row, Col, Card, Image, ConfigProvider, App } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import AuthService from '../services/authService';
import loginImage from '../assets/images/login_img.png';
import { getErrorMessage, errorMap } from '../utils/errorUtils';

const { Title, Paragraph } = Typography;

const RegisterPage = () => {
  const { message: messageApi } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  const onFinish = async (values) => {
    setLoading(true);
    setError(null);
    try {
      const response = await AuthService.register(values.username, values.email, values.password, values.password2);
      messageApi.success(response.message || 'Đăng ký thành công! Vui lòng đăng nhập.');
      navigate('/login');
    } catch (err) {
      console.error("Registration API Error Response:", err);
      const errorMessage = getErrorMessage(err, errorMap);
      setError(errorMessage);
      messageApi.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <div className="w-full h-16 bg-white flex items-center px-6 md:px-8 shadow-sm border-b border-gray-200">
        <Title level={3} style={{ color: '#1f2937', marginBottom: 20, fontWeight: 'bold' }}>NewSumma</Title>
      </div>

      <div className="flex-grow flex items-center justify-center p-4 sm:p-6 md:p-8">
        <Row gutter={[50, 32]} className="w-full max-w-6xl items-center justify-center">
          {/* Cột form đăng ký */}
          <Col xs={{ span: 24, offset: 0 }} sm={{ span: 18, offset: 1 }} md={{ span: 12, offset: 2 }} lg={{ span: 10, offset: 2 }} xl={{ span: 8, offset: 3 }} className="mr-0 sm:mr-4 md:mr-8 lg:mr-12">
            <ConfigProvider 
              theme={{
                token: { colorPrimary: '#1f2937' },
                components: {
                    Button: {
                        colorPrimary: '#252525',
                        colorPrimaryHover: '#374151',
                        colorPrimaryActive: '#111827',
                        colorPrimaryBorder: '#252525',
                    },
                    Alert: {
                        colorErrorBg: '#ef4444',
                        colorErrorBorder: '#dc2626',
                        colorText: '#ffffff',
                        colorTextHeading: '#ffffff',
                        colorIcon: '#ffffff',
                        colorIconHover: '#ffffff',
                    }
                }
              }}
            >
              <Card 
                className="shadow-xl border border-gray-200 w-full" 
                styles={{ body: { padding: '70px 50px' }, width: '120%' }}
              >
                <Title level={4} className="text-gray-500 font-normal mb-2">Bắt đầu nào!</Title>
                <Title level={2} className="text-black mb-2 md:mb-3">Tạo tài khoản</Title>
                <Paragraph className="text-gray-500 mb-8 md:mb-10" style={{ marginBottom: '30px' }}>NewSumma</Paragraph>

                <Spin spinning={loading} tip="Đang xử lý...">
                  <Form
                    form={form}
                    layout="vertical"
                    name="register_form"
                    onFinish={onFinish}
                  >
                    {error && (
                      <Form.Item className="mb-5">
                      </Form.Item>
                    )}

                    <Form.Item
                      label={<span className="text-gray-700">Tên đăng nhập</span>}
                      name="username"
                      rules={[{ required: true, message: 'Vui lòng nhập tên đăng nhập!' }]} 
                      className="mb-5 md:mb-6"
                    >
                      <Input 
                        prefix={<UserOutlined className="text-gray-400" />} 
                        placeholder="Nhập tên đăng nhập mong muốn" 
                        size="large" 
                        className="text-black" 
                      />
                    </Form.Item>
                    
                    <Form.Item
                      label={<span className="text-gray-700">Email</span>}
                      name="email"
                      rules={[
                        { required: true, message: 'Vui lòng nhập email!' },
                        { type: 'email', message: 'Định dạng email không hợp lệ!' }
                      ]}
                      className="mb-5 md:mb-6"
                    >
                      <Input 
                        prefix={<MailOutlined className="text-gray-400" />} 
                        placeholder="Nhập địa chỉ email của bạn" 
                        size="large" 
                        className="text-black" 
                      />
                    </Form.Item>

                    <Form.Item
                      label={<span className="text-gray-700">Mật khẩu</span>}
                      name="password"
                      rules={[
                        { required: true, message: 'Vui lòng nhập mật khẩu!' },
                        { min: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự!' }
                      ]}
                      className="mb-5 md:mb-6"
                      hasFeedback
                    >
                      <Input.Password 
                        prefix={<LockOutlined className="text-gray-400" />} 
                        placeholder="Nhập mật khẩu" 
                        size="large" 
                        className="text-black" 
                      />
                    </Form.Item>

                    <Form.Item
                      label={<span className="text-gray-700">Xác nhận Mật khẩu</span>}
                      name="password2"
                      dependencies={['password']}
                      hasFeedback
                      rules={[
                        { required: true, message: 'Vui lòng xác nhận mật khẩu!' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('password') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('Hai mật khẩu không khớp!'));
                          },
                        }),
                      ]}
                      className="mb-8 md:mb-10"
                    >
                      <Input.Password 
                        prefix={<LockOutlined className="text-gray-400" />} 
                        placeholder="Nhập lại mật khẩu" 
                        size="large" 
                        className="text-black" 
                      />
                    </Form.Item>

                    <Form.Item className="mb-6">
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        className="w-full text-white border-none" 
                        size="large" 
                        disabled={loading}
                        style={{ backgroundColor: '#252525', borderColor: '#252525' }}
                      >
                        Đăng ký
                      </Button>
                    </Form.Item>

                    <div style={{ textAlign: 'center' }}>
                      <span style={{ color: '#8c8c8c' }}>Đã có tài khoản? </span>
                      <a onClick={() => navigate('/login')} style={{ color: '#252525' }}>
                        Đăng nhập
                      </a>
                    </div>
                  </Form>
                </Spin>
              </Card>
            </ConfigProvider>
          </Col>

          {/* Cột ảnh - giữ nguyên hoặc thay đổi */}
          <Col xs={0} sm={0} md={12} lg={14} xl={10} className="hidden md:flex items-center justify-center">
            <Image
              src={loginImage}
              alt="Registration Illustration"
              preview={false}
              style={{ 
                width: '120%', 
                maxWidth: '3000px', 
                height: 'auto' 
              }}
            />
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default RegisterPage; 