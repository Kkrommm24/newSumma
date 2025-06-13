import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Typography, Spin, Row, Col, Card, ConfigProvider, App } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import axiosInstance from '../services/axiosInstance'; // Sử dụng axiosInstance đã cấu hình
import { getErrorMessage, errorMap } from '../utils/errorUtils';

const { Title, Paragraph, Link } = Typography;

const ForgotPasswordPage = () => {
  const { message: messageApi } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [isCoolingDown, setIsCoolingDown] = useState(false);
  const [cooldownTime, setCooldownTime] = useState(0);
  const navigate = useNavigate();
  const intervalRef = useRef(null); // Ref để lưu interval ID

  // Dọn dẹp interval khi component unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const startCooldown = () => {
    setIsCoolingDown(true);
    setCooldownTime(30);
    intervalRef.current = setInterval(() => {
      setCooldownTime((prevTime) => {
        if (prevTime <= 1) {
          clearInterval(intervalRef.current);
          setIsCoolingDown(false);
          return 0;
        }
        return prevTime - 1;
      });
    }, 1000);
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await axiosInstance.post('/user/request-password-reset/', {
        email: values.email,
      });
      messageApi.success(response.data?.message || 'Nếu email tồn tại, bạn sẽ nhận được link đặt lại mật khẩu.');
      startCooldown();
    } catch (err) {
      const errorMessage = getErrorMessage(err, errorMap);
      messageApi.error(errorMessage || 'Yêu cầu đặt lại mật khẩu thất bại. Vui lòng thử lại.');
      console.error("Forgot password request failed:", err.response || err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <div className="w-full h-16 bg-white flex items-center px-6 md:px-8 shadow-sm border-b border-gray-200">
        <Title level={3} style={{ color: '#1f2937', marginBottom: 0, fontWeight: 'bold' }} onClick={() => navigate('/')} className="cursor-pointer">NewSumma</Title>
      </div>

      <div className="flex-grow flex items-center justify-center p-4 sm:p-6 md:p-8">
        <Row justify="center" className="w-full">
          <Col xs={24} sm={16} md={12} lg={8} xl={6}>
             <ConfigProvider
              theme={{
                token: { colorPrimary: '#1f2937' },
                components: { Button: { colorPrimary: '#252525', colorPrimaryHover: '#374151' } }
              }}
            >
              <Card className="shadow-xl border border-gray-200 w-full" styles={{ body: { padding: '40px 30px' } }}>
                <Title level={3} className="text-center text-black mb-4">Quên Mật khẩu</Title>
                <Paragraph className="text-center text-gray-500 mb-8">
                  Nhập địa chỉ email của bạn. Chúng tôi sẽ gửi cho bạn một liên kết để đặt lại mật khẩu.
                </Paragraph>

                <Spin spinning={loading} tip="Đang xử lý...">
                  <Form
                    layout="vertical"
                    name="forgot_password_form"
                    onFinish={onFinish}
                  >
                    <Form.Item
                      label={<span className="text-gray-700">Email</span>}
                      name="email"
                      rules={[
                        { required: true, message: 'Vui lòng nhập email!' },
                        { type: 'email', message: 'Email không hợp lệ!' }
                      ]}
                      className="mb-6"
                    >
                      <Input
                        prefix={<MailOutlined className="text-gray-400" />}
                        placeholder="Nhập địa chỉ email của bạn"
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
                        disabled={loading || isCoolingDown}
                        style={{ backgroundColor: '#252525', borderColor: '#252525' }}
                      >
                        {isCoolingDown ? (
                          <span style={{ color: 'white' }}>{`Thử lại sau ${cooldownTime}s`}</span>
                        ) : (
                          'Gửi liên kết đặt lại'
                        )}
                      </Button>
                    </Form.Item>

                    <div className="text-center">
                      <Link 
                        onClick={() => navigate('/login')} 
                        className="hover:text-gray-700" 
                        style={{ color: '#252525', textDecoration: 'underline' }} 
                      >
                        Quay lại Đăng nhập
                      </Link>
                    </div>
                  </Form>
                </Spin>
              </Card>
            </ConfigProvider>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default ForgotPasswordPage; 