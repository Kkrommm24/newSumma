import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Form, Input, Button, Typography, Spin, Row, Col, Card, ConfigProvider, App } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import axiosInstance from '../services/axiosInstance';
import { getErrorMessage, errorMap } from '../utils/errorUtils';

const { Title, Paragraph } = Typography;

const ResetPasswordPage = () => {
    const { message: messageApi } = App.useApp();
    const [loading, setLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const navigate = useNavigate();
    const { reset_token } = useParams();
    const [form] = Form.useForm();

    useEffect(() => {
        if (!reset_token) {
            messageApi.error('Thiếu thông tin đặt lại mật khẩu. Vui lòng thử lại từ liên kết trong email.');
            navigate('/login');
        }
    }, [reset_token, navigate, messageApi]);

    const onFinish = async (values) => {
        if (!reset_token) {
            messageApi.error('Token đặt lại không hợp lệ.');
            return;
        }
        setLoading(true);
        try {
            const response = await axiosInstance.post('/user/password-reset-confirm/', {
                password: values.password,
                password2: values.password2,
                reset_token: reset_token,
            });
            messageApi.success(response.data?.message || 'Đặt lại mật khẩu thành công!');
            setIsSuccess(true);
            setTimeout(() => {
                navigate('/login');
            }, 3000);

        } catch (err) {
            console.error("Reset password confirmation failed:", err);
            messageApi.error(getErrorMessage(err, errorMap));
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
                                <Title level={3} className="text-center text-black mb-4">Đặt Lại Mật Khẩu</Title>
                                <Paragraph className="text-center text-gray-500 mb-8">
                                    {isSuccess ? 'Bạn sẽ được chuyển hướng đến trang đăng nhập sau giây lát.' : 'Nhập mật khẩu mới cho tài khoản của bạn.'}
                                </Paragraph>
                                <Spin spinning={loading} tip="Đang xử lý...">
                                    <Form
                                        form={form}
                                        layout="vertical"
                                        name="reset_password_form"
                                        onFinish={onFinish}
                                        disabled={isSuccess}
                                    >
                                        <Form.Item
                                            label={<span className="text-gray-700">Mật khẩu mới</span>}
                                            name="password"
                                            rules={[
                                                { required: true, message: 'Vui lòng nhập mật khẩu mới!' },
                                                { min: 8, message: 'Mật khẩu phải có ít nhất 8 ký tự!' }
                                            ]}
                                            hasFeedback
                                            className="mb-6"
                                        >
                                            <Input.Password
                                                prefix={<LockOutlined className="text-gray-400" />}
                                                placeholder="Nhập mật khẩu mới"
                                                size="large"
                                                className="text-black"
                                            />
                                        </Form.Item>
                                        <Form.Item
                                            label={<span className="text-gray-700">Xác nhận mật khẩu mới</span>}
                                            name="password2"
                                            dependencies={['password']}
                                            hasFeedback
                                            rules={[
                                                { required: true, message: 'Vui lòng xác nhận mật khẩu mới!' },
                                                ({ getFieldValue }) => ({
                                                    validator(_, value) {
                                                        if (!value || getFieldValue('password') === value) {
                                                            return Promise.resolve();
                                                        }
                                                        return Promise.reject(new Error('Mật khẩu xác nhận không khớp!'));
                                                    },
                                                }),
                                            ]}
                                            className="mb-6"
                                        >
                                            <Input.Password
                                                prefix={<LockOutlined className="text-gray-400" />}
                                                placeholder="Xác nhận mật khẩu mới"
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
                                                disabled={loading || !reset_token}
                                                style={{ backgroundColor: '#252525', borderColor: '#252525' }}
                                            >
                                                Đặt Lại Mật Khẩu
                                            </Button>
                                        </Form.Item>
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

export default ResetPasswordPage; 