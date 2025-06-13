import React, { useState, useEffect, useCallback } from 'react';
import { Card, Form, Input, Button, Avatar, Upload, Modal, Spin, Typography, Space, Row, Col, App } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined, UploadOutlined, ExclamationCircleFilled } from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import AuthService from '../services/authService';
import { getErrorMessage, errorMap } from '../utils/errorUtils';

const { Title } = Typography;

function Profile() {
    const { message: messageApi, modal: modalApi } = App.useApp();
    const [profileForm] = Form.useForm();
    const [passwordForm] = Form.useForm();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false);
    const [changingPassword, setChangingPassword] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [fileList, setFileList] = useState([]);
    const [changePasswordModalVisible, setChangePasswordModalVisible] = useState(false);
    const [previewImage, setPreviewImage] = useState(null);

    const { logout } = useAuth();

    useEffect(() => {
        let isMounted = true;
        const fetchProfile = async () => {
            try {
                setLoading(true);
                const data = await AuthService.getUserProfile();
                if (isMounted) {
                    setProfile(data);
                }
            } catch (error) {
                if (isMounted) {
                    console.error("Failed to fetch profile:", error);
                    messageApi.error(getErrorMessage(error, errorMap));
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };
        fetchProfile();
        return () => {
            isMounted = false;
        };
    }, []);

    useEffect(() => {
        if (profile) {
            profileForm.setFieldsValue(profile);
            setPreviewImage(profile.avatar);
        }
    }, [profile, profileForm]);

    const handleProfileUpdate = async (values) => {
        setUpdating(true);
        const formData = new FormData();
        let hasChanges = false;

        if (values.username !== profile.username) {
             formData.append('username', values.username);
             hasChanges = true;
        }
        if (values.email !== profile.email) {
             formData.append('email', values.email);
             hasChanges = true;
        }
        if (fileList.length > 0 && fileList[0].originFileObj) {
            formData.append('avatar', fileList[0].originFileObj);
            hasChanges = true;
        }

        if (!hasChanges) {
            messageApi.info("Không có thay đổi nào để cập nhật.");
            setUpdating(false);
            return;
        }

        try {
            const data = await AuthService.updateUserProfile(formData);
            setProfile(data);
            profileForm.setFieldsValue(data);
            setPreviewImage(data.avatar);
            setFileList([]);
            messageApi.success('Cập nhật hồ sơ thành công!');
        } catch (error) {
            console.error("Failed to update profile:", error);
            messageApi.error(getErrorMessage(error, errorMap));
        } finally {
            setUpdating(false);
        }
    };

    const handlePasswordChange = async (values) => {
        setChangingPassword(true);
        try {
            const response = await AuthService.changePassword(values);
            messageApi.success(response?.message || 'Đổi mật khẩu thành công!');
            setChangePasswordModalVisible(false);
            passwordForm.resetFields();
        } catch (error) {
            console.error("Failed to change password:", error);
            messageApi.error(getErrorMessage(error, errorMap));
        } finally {
            setChangingPassword(false);
        }
    };

    const showDeleteConfirm = () => {
        let passwordInput = '';
        modalApi.confirm({
            title: 'Bạn có chắc chắn muốn xóa tài khoản?',
            icon: <ExclamationCircleFilled />,
            content: (
                <div>
                    <p>Hành động này không thể hoàn tác. Tài khoản của bạn sẽ bị vô hiệu hóa.</p>
                    <p>Vui lòng nhập mật khẩu để xác nhận:</p>
                    <Input.Password 
                        placeholder="Mật khẩu"
                        onChange={(e) => passwordInput = e.target.value} 
                        autoComplete="new-password"
                    />
                </div>
            ),
            okText: 'Xác nhận xóa',
            okType: 'danger',
            cancelText: 'Hủy bỏ',
            onOk: async () => {
                if (!passwordInput) {
                    messageApi.error('Vui lòng nhập mật khẩu để xác nhận.');
                    throw new Error('Password required');
                }
                setDeleting(true);
                try {
                    const response = await AuthService.deleteAccount(passwordInput);
                    messageApi.success(response?.message || 'Tài khoản đã được vô hiệu hóa.');
                    setDeleting(false);
                    logout();
                } catch (error) { 
                    console.error("Failed to delete account:", error);
                    messageApi.error(getErrorMessage(error, errorMap));
                    setDeleting(false);
                    throw error;
                }
            },
        });
    };

    const handleUploadChange = ({ fileList: newFileList }) => {
        const newFile = newFileList[newFileList.length - 1];
        if (newFile) {
            if (newFile.originFileObj) {
                const reader = new FileReader();
                reader.onload = (e) => setPreviewImage(e.target.result);
                reader.readAsDataURL(newFile.originFileObj);
            } else if (newFile.url) {
                setPreviewImage(newFile.url);
            }
            setFileList([newFile]);
        } else {
            setFileList([]);
            setPreviewImage(profile?.avatar);
        }
    };

    if (loading) {
        return <Spin size="large" style={{ display: 'block', marginTop: '50px' }} />;
    }

    if (!profile) {
        return <Title level={3}>Không thể tải thông tin cá nhân.</Title>;
    }

    return (
        <Card>
            <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
                <Col>
                    <Title level={3} style={{ marginBottom: 0 }}>Trang cá nhân</Title>
                </Col>
                <Col>
                    <Space direction="vertical" align="center">
                        <Avatar size={100} src={previewImage} icon={<UserOutlined />} />
                        <Upload
                            accept="image/*"
                            listType="picture"
                            fileList={fileList}
                            onChange={handleUploadChange}
                            maxCount={1}
                            showUploadList={false}
                        >
                            <Button icon={<UploadOutlined />}>Thay đổi ảnh</Button>
                        </Upload>
                    </Space>
                </Col>
            </Row>

            <Form
                form={profileForm}
                layout="vertical"
                onFinish={handleProfileUpdate}
                initialValues={profile}
            >
                <Form.Item
                    name="username"
                    label="Tên người dùng"
                    rules={[{ required: true, message: 'Vui lòng nhập tên người dùng!' }]}
                >
                    <Input prefix={<UserOutlined />} placeholder="Tên người dùng" />
                </Form.Item>
                <Form.Item
                    name="email"
                    label="Email"
                    rules={[{ required: true, type: 'email', message: 'Vui lòng nhập email hợp lệ!' }]}
                >
                    <Input prefix={<MailOutlined />} placeholder="Email" />
                </Form.Item>
                <Form.Item style={{ marginTop: 24 }}>
                     <Space size="middle" wrap>
                        <Button 
                            type="primary" 
                            htmlType="submit" 
                            loading={updating}
                            style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
                        >
                            Cập nhật thông tin
                        </Button>
                        <Button 
                            onClick={() => setChangePasswordModalVisible(true)}
                            style={{ color: '#252525', borderColor: '#252525' }}
                        >
                            Đổi mật khẩu
                        </Button>
                        <Button 
                            type="primary"
                            danger
                            onClick={showDeleteConfirm} 
                            loading={deleting}
                            style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
                        >
                            Xóa tài khoản
                        </Button>
                     </Space>
                </Form.Item>
            </Form>

            <Modal
                title="Đổi mật khẩu"
                open={changePasswordModalVisible}
                onCancel={() => setChangePasswordModalVisible(false)}
                footer={null}
                destroyOnClose
            >
                <Form
                    form={passwordForm}
                    layout="vertical"
                    onFinish={handlePasswordChange}
                >
                    <Form.Item
                        name="old_password"
                        label="Mật khẩu cũ"
                        rules={[{ required: true, message: 'Vui lòng nhập mật khẩu cũ!' }]}
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="Mật khẩu cũ" />
                    </Form.Item>
                    <Form.Item
                        name="new_password"
                        label="Mật khẩu mới"
                        rules={[{ required: true, message: 'Vui lòng nhập mật khẩu mới!' }]}
                    >
                        <Input.Password prefix={<LockOutlined />} placeholder="Mật khẩu mới" />
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
                        <Input.Password prefix={<LockOutlined />} placeholder="Xác nhận mật khẩu mới" />
                    </Form.Item>
                    <Form.Item>
                        <Button 
                            type="primary" 
                            htmlType="submit" 
                            loading={changingPassword}
                            style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
                        >
                            Xác nhận đổi mật khẩu
                        </Button>
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
}

export default Profile;
