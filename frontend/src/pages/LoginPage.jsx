import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Typography, Spin, Alert, Row, Col, Checkbox, Card, Image, ConfigProvider } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../context/AuthContext.jsx';
import AuthService from '../services/authService';
import axiosInstance from '../services/axiosInstance';
import loginImage from '../assets/images/login_img.png';

const { Title, Paragraph, Link } = Typography;

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [checkingPrefs, setCheckingPrefs] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { login, authLoading } = useAuth();

  const from = location.state?.from?.pathname || "/";

  const onFinish = async (values) => {
    setLoading(true);
    setError('');
    try {
      const loginData = await AuthService.login(values.username, values.password);

      if (loginData && loginData.access && loginData.user) {
        const loginSuccess = await login(loginData.access, loginData.refresh, loginData.user);

        if (loginSuccess) {
          setCheckingPrefs(true);
          try {
            const prefsResponse = await axiosInstance.get('/user/fav-words/');
            const favoriteKeywords = prefsResponse.data?.favorite_keywords || [];
            
            if (favoriteKeywords.length === 0) {
              navigate('/favourite-categories', { replace: true });
            } else {
              navigate(from, { replace: true });
            }
          } catch (prefsError) {
            navigate(from, { replace: true });
          } finally {
            setCheckingPrefs(false);
          }
        } else {
          setError('Đã xảy ra lỗi khi xử lý thông tin đăng nhập.');
        }
      } else {
        setError('Dữ liệu đăng nhập không hợp lệ từ server.');
      }
    } catch (error) {
      const defaultErrorMessage = 'Đăng nhập thất bại. Vui lòng kiểm tra lại tên đăng nhập và mật khẩu.';
      const backendError = error.response?.data?.detail || defaultErrorMessage;
      setError(backendError);
    } finally {
      setLoading(false);
    }
  };

  const totalLoading = loading || authLoading || checkingPrefs;
  const loadingTip = authLoading ? "Đang xử lý..." : (checkingPrefs ? "Kiểm tra cài đặt..." : "Đang đăng nhập...");

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <div className="w-full h-16 bg-white flex items-center px-6 md:px-8 shadow-sm border-b border-gray-200">
        <Title level={3} style={{ color: '#1f2937', marginBottom: 20, fontWeight: 'bold' }}>NewSumma</Title>
      </div>

      <div className="flex-grow flex items-center justify-center p-4 sm:p-6 md:p-8">
        <Row gutter={[50, 32]} className="w-full max-w-6xl items-center justify-center">
          <Col xs={{ span: 24, offset: 0 }}
            sm={{ span: 18, offset: 1 }}
            md={{ span: 12, offset: 2 }}
            lg={{ span: 10, offset: 2 }}
            xl={{ span: 8, offset: 3 }}
            className="mr-0 sm:mr-4 md:mr-8 lg:mr-12"
          >
            <ConfigProvider
              theme={{
                token: {
                  colorPrimary: '#1f2937',
                },
                components: {
                  Checkbox: {
                    colorPrimary: '#1f2937',
                    colorPrimaryHover: '#111827',
                  },
                  Input: {
                    colorPrimary: '#1f2937',
                    colorPrimaryHover: '#111827'
                  },
                  Button: {
                    colorPrimary: '#252525',
                    colorPrimaryHover: '#374151',
                    colorPrimaryActive: '#111827',
                    colorPrimaryBorder: '#252525',
                  }
                }
              }}
            >
              <Card
                className="shadow-xl border border-gray-200 w-full"
                styles={{ body: { padding: '70px 50px' }, width: '120%', }}
              >
                <Title level={4} className="text-gray-500 font-normal mb-2">Chào mừng!</Title>
                <Title level={2} className="text-black mb-2 md:mb-3">Đăng nhập vào</Title>
                <Paragraph className="text-gray-500 mb-8 md:mb-10" style={{ marginBottom: '30px' }}>NewSumma</Paragraph>

                <Spin spinning={totalLoading} tip={loadingTip}>
                  <Form
                    layout="vertical"
                    name="login_form"
                    initialValues={{ remember: false }}
                    onFinish={onFinish}
                  >
                    {error && (
                      <Form.Item className="mb-5">
                        <Alert message={error} type="error" showIcon />
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
                        placeholder="Nhập tên đăng nhập của bạn"
                        size="large"
                        className="text-black"
                      />
                    </Form.Item>

                    <Form.Item
                      label={<span className="text-gray-700">Mật khẩu</span>}
                      name="password"
                      rules={[{ required: true, message: 'Vui lòng nhập mật khẩu!' }]}
                      className="mb-3 md:mb-4"
                    >
                      <Input.Password
                        prefix={<LockOutlined className="text-gray-400" />}
                        placeholder="Nhập mật khẩu của bạn"
                        size="large"
                        className="text-black"
                      />
                    </Form.Item>

                    <Form.Item className="mb-8 md:mb-10">
                      <Row justify="space-between">
                        <Col>
                          <Form.Item name="remember" valuePropName="checked" noStyle>
                            <Checkbox className="text-gray-700">Lưu mật khẩu</Checkbox>
                          </Form.Item>
                        </Col>
                        <Col>
                          <a
                            onClick={() => navigate('/forgot-password')}
                            style={{ color: '#252525' }}
                          >
                            Quên mật khẩu?
                          </a>
                        </Col>
                      </Row>
                    </Form.Item>

                    <Form.Item className="mb-6">
                      <Button
                        type="primary"
                        htmlType="submit"
                        className="w-full text-white border-none"
                        size="large"
                        disabled={totalLoading}
                        style={{
                            backgroundColor: '#252525',
                            borderColor: '#252525'
                        }}
                      >
                        Đăng nhập
                      </Button>
                    </Form.Item>

                    <div style={{ textAlign: 'center' }}>
                      <span style={{ color: '#8c8c8c' }}>Chưa có tài khoản? </span>
                      <a
                        onClick={() => navigate('/register')}
                        style={{ color: '#252525' }}
                      >
                        Đăng ký
                      </a>
                    </div>
                  </Form>
                </Spin>
              </Card>
            </ConfigProvider>
          </Col>

          <Col xs={0} sm={0} md={12} lg={14} xl={10} className="hidden md:flex items-center justify-center">
            <Image
              src={loginImage}
              alt="Login Illustration"
              preview={false}
              style={{
                width: '120%',
                maxWidth: '3000px',
                height: 'auto',
                // marginLeft: '30px'
              }}
            />
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default LoginPage; 