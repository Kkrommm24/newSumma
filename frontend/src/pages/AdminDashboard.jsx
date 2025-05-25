import React, { useState, useEffect } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Button, Table, Space, Modal, Typography, Image, App, Spin } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  FileSearchOutlined,
  SyncOutlined,
  DeleteOutlined,
  LogoutOutlined,
  LockOutlined,
  ArrowLeftOutlined,
  CommentOutlined,
  TagsOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../services/axiosInstance';
import { useAuth } from '../context/AuthContext';
import { useDispatch, useSelector } from 'react-redux';
import { resetUserState } from '../store/slices/userSlice';
import {
  setStats,
  setUsers,
  setArticles,
  setSummaries,
  setComments,
  setFavoriteWords,
  setKeywordUsers,
  setLoading,
  setPagination,
  setKeywordUsersPagination,
  setSelectedKeyword,
  resetAdminState
} from '../store/slices/adminSlice';
import logo from '../assets/images/logo.png';
import ChangePasswordModal from '../components/ChangePasswordModal';
import NewsCard from '../components/NewsCard';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const AdminDashboard = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedMenu, setSelectedMenu] = useState(() => {
    // Lấy menu đã chọn từ localStorage khi khởi tạo
    return localStorage.getItem('adminSelectedMenu') || 'dashboard';
  });
  const [changePasswordVisible, setChangePasswordVisible] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);

  const { user, logout: authLogout } = useAuth();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message, modal } = App.useApp();

  // Lấy state từ Redux
  const {
    stats,
    users,
    articles,
    summaries,
    comments,
    favoriteWords,
    keywordUsers,
    loading,
    pagination,
    keywordUsersPagination,
    selectedKeyword
  } = useSelector(state => state.admin);

  // Thêm state để lưu trữ tất cả các giá trị cho filter
  const [allFilterValues, setAllFilterValues] = useState({
    users: { usernames: [], emails: [] },
    articles: { titles: [], sources: [] },
    summaries: { articleTitles: [] },
    comments: { usernames: [], articleTitles: [] }
  });

  const handleTableChange = (pagination, filters, sorter) => {
    
    // Lưu trạng thái phân trang và filter vào localStorage
    localStorage.setItem('adminPagination', JSON.stringify({
      current: pagination.current,
      pageSize: pagination.pageSize,
      filters: filters,
      sorter: sorter
    }));
    
    // Tạo query params cho filter
    let queryParams = `page=${pagination.current}&page_size=${pagination.pageSize}`;
    
    // Thêm các filter vào query params
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value.length > 0) {
        // Xử lý riêng cho source_name
        if (key === 'source_name') {
          queryParams += `&source_name=${value.join(',')}`;
        } else {
          queryParams += `&${key}=${value.join(',')}`;
        }
      }
    });
    
    // Thêm sorter vào query params nếu có
    if (sorter.field && sorter.order) {
      queryParams += `&ordering=${sorter.order === 'descend' ? '-' : ''}${sorter.field}`;
    }
    
    fetchData(pagination.current, pagination.pageSize, queryParams);
  };

  const fetchData = async (page = 1, pageSize = 10, queryParams = '') => {
    try {
      dispatch(setLoading(true));
      
      // Luôn gọi API dashboard để lấy thống kê
      const statsRes = await axiosInstance.get('/user/admin/dashboard/');
      dispatch(setStats(statsRes.data));

      // Chỉ gọi API cho tab đang được chọn
      let paginationData = null;
      let response = null;

      switch (selectedMenu) {
        case 'users':
          response = await axiosInstance.get(`/user/admin/users/?${queryParams}`);
          dispatch(setUsers(response.data.results));
          paginationData = response.data;
          break;
        case 'articles':
          response = await axiosInstance.get(`/user/admin/articles/?${queryParams}`);
          dispatch(setArticles(response.data.results));
          paginationData = response.data;
          break;
        case 'summaries':
          response = await axiosInstance.get(`/user/admin/summaries/?${queryParams}`);
          dispatch(setSummaries(response.data.results));
          paginationData = response.data;
          break;
        case 'comments':
          response = await axiosInstance.get(`/user/admin/comments/?${queryParams}`);
          dispatch(setComments(response.data.results));
          paginationData = response.data;
          break;
        case 'fav-words':
          response = await axiosInstance.get(`/user/admin/fav-words/?${queryParams}`);
          dispatch(setFavoriteWords(response.data.results));
          paginationData = response.data;
          break;
        default:
          break;
      }

      if (paginationData) {
        // Tính toán số trang tối đa
        const maxPage = Math.ceil(paginationData.count / pageSize);
        
        // Nếu trang hiện tại vượt quá số trang tối đa, reset về trang 1
        if (page > maxPage) {
          localStorage.setItem('adminPagination', JSON.stringify({
            current: 1,
            pageSize: pageSize
          }));
          fetchData(1, pageSize);
          return;
        }
        
        // Cập nhật state pagination
        dispatch(setPagination({
          current: page,
          pageSize: pageSize,
          total: paginationData.count,
          showSizeChanger: false,
          hideOnSinglePage: false,
          pageSizeOptions: ['10'],
          showQuickJumper: true
        }));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      let errorMessage = 'Lỗi khi tải dữ liệu';
      
      if (error.response) {
        // Lỗi từ server
        errorMessage = error.response.data?.error || error.response.data?.detail || errorMessage;
        console.error('Server error details:', error.response.data);
      } else if (error.request) {
        // Không nhận được response
        errorMessage = 'Không thể kết nối đến server';
        console.error('Network error:', error.request);
      } else {
        // Lỗi khi setup request
        console.error('Request setup error:', error.message);
      }
      
      message.error(errorMessage);
      
      // Reset về trang 1 nếu có lỗi
      dispatch(setPagination({
        current: 1,
        pageSize: 10,
        total: 0,
        showSizeChanger: false,
        hideOnSinglePage: false,
        pageSizeOptions: ['10'],
        showQuickJumper: true
      }));
    } finally {
      dispatch(setLoading(false));
    }
  };

  useEffect(() => {
    if (!user?.is_staff) {
      navigate('/');
      return;
    }
    // Chỉ gọi API dashboard khi component mount
    const fetchInitialData = async () => {
      try {
        const statsRes = await axiosInstance.get('/user/admin/dashboard/');
        dispatch(setStats(statsRes.data));
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        message.error('Lỗi khi tải thống kê');
      }
    };
    
    fetchInitialData();
    
    return () => {
      dispatch(resetAdminState());
    };
  }, [user, navigate]);

  // Thêm useEffect để lưu selectedMenu vào localStorage khi nó thay đổi
  useEffect(() => {
    localStorage.setItem('adminSelectedMenu', selectedMenu);
  }, [selectedMenu]);

  // Sửa lại useEffect để khôi phục trạng thái phân trang từ localStorage
  useEffect(() => {
    const savedPagination = localStorage.getItem('adminPagination');
    if (savedPagination) {
      try {
        const { current, pageSize, filters, sorter } = JSON.parse(savedPagination);
        // Kiểm tra tính hợp lệ của trang
        if (current > 0 && pageSize > 0) {
          // Reset về trang 1 nhưng giữ nguyên filters và sorter
          fetchData(1, pageSize, `page=1&page_size=${pageSize}${filters ? `&${Object.entries(filters).map(([key, value]) => `${key}=${value.join(',')}`).join('&')}` : ''}${sorter ? `&ordering=${sorter.order === 'descend' ? '-' : ''}${sorter.field}` : ''}`);
        } else {
          throw new Error('Invalid pagination data');
        }
      } catch (error) {
        console.error('Error parsing pagination data:', error);
        localStorage.removeItem('adminPagination');
        fetchData(1, 10);
      }
    } else {
      // Nếu không có dữ liệu trong localStorage, bắt đầu với trang 1
      fetchData(1, 10);
    }
  }, [selectedMenu]); // Thêm selectedMenu vào dependencies để fetch lại data khi chuyển tab

  const handleCrawl = async (source) => {
    try {
      await axiosInstance.post('/user/admin/crawl/', { source });
      message.success(`Đã bắt đầu crawl từ ${source}`);
    } catch (error) {
      message.error('Lỗi khi kích hoạt crawl');
    }
  };

  const handleSummarize = async (articleId = null) => {
    try {
      if (articleId) {
        await axiosInstance.post(`/summarizer/summaries/trigger-single/${articleId}/`);
        message.success('Đã bắt đầu tạo tóm tắt cho bài viết được chọn');
      } else {
        modal.confirm({
          title: 'Xác nhận tạo tóm tắt',
          content: 'Hệ thống sẽ tạo tóm tắt cho tối đa 10 bài viết chưa có tóm tắt. Bạn có muốn tiếp tục?',
          onOk: async () => {
            try {
              await axiosInstance.post('/summarizer/summaries/trigger-bulk/');
              message.success('Đã bắt đầu tạo tóm tắt cho tối đa 10 bài viết');
            } catch (error) {
              message.error('Lỗi khi kích hoạt tóm tắt');
            }
          }
        });
      }
    } catch (error) {
      message.error('Lỗi khi kích hoạt tóm tắt');
    }
  };

  const handleDelete = async (type, id) => {
    modal.confirm({
      title: 'Xác nhận xóa',
      content: 'Bạn có chắc chắn muốn xóa mục này?',
      onOk: async () => {
        try {
          await axiosInstance.delete(`/user/admin/${type}/${id}/`);
          message.success('Xóa thành công');
          fetchData();
        } catch (error) {
          message.error('Lỗi khi xóa');
        }
      }
    });
  };

  const handleLogout = async () => {
    try {
      authLogout();
      dispatch(resetUserState());
      message.success('Đăng xuất thành công');
      navigate('/login');
    } catch (error) {
      message.error('Lỗi khi đăng xuất');
    }
  };

  const handleDeleteUser = (user) => {
    if (user.is_staff) {
      message.error('Không thể khóa tài khoản admin');
      return;
    }

    modal.confirm({
      title: `Xác nhận ${user.is_active ? 'khóa' : 'mở khóa'} tài khoản`,
      content: `Bạn có chắc chắn muốn ${user.is_active ? 'khóa' : 'mở khóa'} tài khoản của ${user.username}?`,
      onOk: async () => {
        try {
          const response = await axiosInstance.patch(`/user/admin/users/${user.id}/`, {
            is_active: !user.is_active
          });
          
          if (response.data) {
            message.success(`Đã ${user.is_active ? 'khóa' : 'mở khóa'} tài khoản thành công`);
            // Gọi lại fetchData để làm mới dữ liệu bảng users và pagination
            // Lấy thông tin pagination, filters, sorter hiện tại
            const currentPaginationState = pagination; // Từ Redux state admin.pagination
            const savedAdminPaginationConfig = JSON.parse(localStorage.getItem('adminPagination')) || {};
            const currentFilters = savedAdminPaginationConfig.filters || {};
            const currentSorter = savedAdminPaginationConfig.sorter || {};

            let queryParamsString = `page=${currentPaginationState.current}&page_size=${currentPaginationState.pageSize}`;
            
            Object.entries(currentFilters).forEach(([key, value]) => {
              if (value && value.length > 0) {
                // Xử lý riêng cho source_name nếu cần, hoặc backend tự xử lý
                // if (key === 'source_name') {
                //   queryParamsString += `&source_name=${value.join(',')}`;
                // } else {
                queryParamsString += `&${key}=${value.join(',')}`;
                // }
              }
            });
            
            if (currentSorter.field && currentSorter.order) {
              queryParamsString += `&ordering=${currentSorter.order === 'descend' ? '-' : ''}${currentSorter.field}`;
            }
            
            fetchData(currentPaginationState.current, currentPaginationState.pageSize, queryParamsString);
          }
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Lỗi khi thực hiện thao tác';
          message.error(errorMessage);
        }
      }
    });
  };

  const handleSummaryClick = async (summary) => {
    setSelectedSummary(summary);
    setDetailLoading(true);
    setDetailError(null);
    try {
      const response = await axiosInstance.get(`/news/summaries/${summary.id}/`);
      setSelectedArticle(response.data);
    } catch (error) {
      setDetailError('Không thể tải chi tiết tóm tắt');
      console.error('Error fetching summary details:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleBackToList = () => {
    setSelectedSummary(null);
    setSelectedArticle(null);
    setDetailError(null);
  };

  const handleKeywordClick = async (keyword) => {
    dispatch(setSelectedKeyword(keyword));
    dispatch(setLoading(true));
    try {
      const response = await axiosInstance.get(`/user/admin/fav-words/?keyword=${encodeURIComponent(keyword)}`);
      dispatch(setKeywordUsers(response.data.results));
      
      dispatch(setKeywordUsersPagination({
        current: 1,
        pageSize: 10,
        total: response.data.count || 0,
        showSizeChanger: false,
        hideOnSinglePage: false
      }));
    } catch (error) {
      console.error('Error fetching keyword users:', error);
      message.error('Lỗi khi tải danh sách người dùng');
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleKeywordUsersTableChange = (pagination, filters, sorter) => {
    dispatch(setKeywordUsersPagination(pagination));
    // Gọi API để lấy dữ liệu cho trang mới
    axiosInstance.get(`/user/admin/fav-words/?keyword=${encodeURIComponent(selectedKeyword)}&page=${pagination.current}&page_size=${pagination.pageSize}`)
      .then(response => {
        dispatch(setKeywordUsers(response.data.results));
        dispatch(setKeywordUsersPagination({
          current: response.data.current_page,
          pageSize: pagination.pageSize,
          total: response.data.count,
          showSizeChanger: false,
          hideOnSinglePage: false,
          showTotal: (total, range) => `${range[0]}-${range[1]} của ${total} mục`,
          pageSizeOptions: ['10'],
          showQuickJumper: true
        }));
      })
      .catch(error => {
        console.error('Error fetching keyword users page:', error);
        message.error('Lỗi khi tải danh sách người dùng');
      });
  };

  const handleBackToKeywords = () => {
    dispatch(setSelectedKeyword(null));
    dispatch(setKeywordUsers([]));
    dispatch(setKeywordUsersPagination({
      current: 1,
      pageSize: 10,
      total: 0
    }));
  };

  const userColumns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      sorter: true,
      filters: [],
      onFilter: (value, record) => record.username === value,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: true,
      filters: [],
      onFilter: (value, record) => record.email === value,
    },
    {
      title: 'Trạng thái',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <span style={{ color: isActive ? 'green' : 'red' }}>
          {isActive ? 'Hoạt động' : 'Khóa'}
        </span>
      ),
      filters: [
        { text: 'Hoạt động', value: true },
        { text: 'Khóa', value: false }
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString('vi-VN'),
      sorter: true,
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_, record) => (
        <Space>
          {!record.is_staff && (
            <Button
              type="primary"
              danger={record.is_active}
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteUser(record)}
              style={{ 
                backgroundColor: record.is_active ? '#ff4d4f' : '#52c41a',
                color: 'white',
                borderColor: record.is_active ? '#ff4d4f' : '#52c41a'
              }}
            >
              {record.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const articleColumns = [
    {
      title: 'Tiêu đề',
      dataIndex: 'title',
      key: 'title',
      sorter: (a, b) => a.title.localeCompare(b.title),
      filters: [],
      onFilter: (value, record) => record.title === value,
      render: (text, record) => (
        <a 
          href={record.url} 
          target="_blank" 
          rel="noopener noreferrer"
          onClick={(e) => {
            e.stopPropagation();
            window.open(record.url, '_blank');
          }}
        >
          {text}
        </a>
      ),
    },
    {
      title: 'Nguồn',
      dataIndex: 'source_name',
      key: 'source_name',
      sorter: true,
      filters: [],
      onFilter: (value, record) => record.source_name === value,
    },
    {
      title: 'Ngày đăng',
      dataIndex: 'published_at',
      key: 'published_at',
      render: (date) => date ? new Date(date).toLocaleDateString('vi-VN') : 'N/A',
      sorter: (a, b) => new Date(a.published_at || 0) - new Date(b.published_at || 0),
    },
    {
      title: 'Ngày cập nhật',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date) => new Date(date).toLocaleString('vi-VN'),
      sorter: (a, b) => new Date(a.updated_at) - new Date(b.updated_at),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={() => handleSummarize(record.id)}
            style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
          >
            {record.has_summary ? 'Tóm tắt lại' : 'Tạo tóm tắt'}
          </Button>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete('articles', record.id)}
            style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
          >
            Xóa
          </Button>
        </Space>
      ),
    },
  ];

  const summaryColumns = [
    {
      title: 'Bài viết',
      dataIndex: 'article_title',
      key: 'article_title',
      sorter: (a, b) => a.article_title.localeCompare(b.article_title),
      filters: [],
      onFilter: (value, record) => record.article_title === value,
      render: (text, record) => (
        <a onClick={() => handleSummaryClick(record)}>{text}</a>
      ),
    },
    {
      title: 'Upvotes',
      dataIndex: 'upvotes',
      key: 'upvotes',
      sorter: (a, b) => a.upvotes - b.upvotes,
    },
    {
      title: 'Downvotes',
      dataIndex: 'downvotes',
      key: 'downvotes',
      sorter: (a, b) => a.downvotes - b.downvotes,
    },
    {
      title: 'Ngày cập nhật',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date) => new Date(date).toLocaleString('vi-VN'),
      sorter: (a, b) => new Date(a.updated_at) - new Date(b.updated_at),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={() => handleSummarize(record.article_id)}
            style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
          >
            Tóm tắt lại
          </Button>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete('summaries', record.id)}
            style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
          >
            Xóa
          </Button>
        </Space>
      ),
    },
  ];

  const commentColumns = [
    {
      title: 'Nội dung',
      dataIndex: 'content',
      key: 'content',
      render: (text) => (
        <div style={{ maxWidth: '300px' }}>
          <Text ellipsis={{ tooltip: text }}>{text}</Text>
        </div>
      ),
    },
    {
      title: 'Người dùng',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
      filters: [],
      onFilter: (value, record) => record.username === value,
    },
    {
      title: 'Bài viết',
      dataIndex: 'article_title',
      key: 'article_title',
      render: (text) => (
        <div style={{ maxWidth: '200px' }}>
          <Text ellipsis={{ tooltip: text }}>{text}</Text>
        </div>
      ),
      filters: [],
      onFilter: (value, record) => record.article_title === value,
    },
    {
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString('vi-VN'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete('comments', record.id)}
            style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
          >
            Xóa
          </Button>
        </Space>
      ),
    },
  ];

  const favoriteWordsColumns = [
    {
      title: 'Từ khóa',
      dataIndex: 'keyword',
      key: 'keyword',
      sorter: true,
      render: (text) => (
        <a onClick={() => handleKeywordClick(text)}>{text}</a>
      ),
    },
    {
      title: 'Số người dùng',
      dataIndex: 'user_count',
      key: 'user_count',
      sorter: true,
    },
    {
      title: 'Thao tác',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete('fav-words', record.keyword)}
            style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
          >
            Xóa
          </Button>
        </Space>
      ),
    },
  ];

  const keywordUsersColumns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: (a, b) => a.email.localeCompare(b.email),
    },
    {
      title: 'Trạng thái',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <span style={{ color: isActive ? 'green' : 'red' }}>
          {isActive ? 'Hoạt động' : 'Khóa'}
        </span>
      ),
    },
    {
      title: 'Ngày tạo',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString('vi-VN'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
  ];

  // Hàm để lấy tất cả các giá trị cho filter
  const fetchAllFilterValues = async () => {
    try {
      const [usersRes, articlesRes, summariesRes, commentsRes] = await Promise.all([
        axiosInstance.get('/user/admin/users/filter-values/'),
        axiosInstance.get('/user/admin/articles/filter-values/'),
        axiosInstance.get('/user/admin/summaries/filter-values/'),
        axiosInstance.get('/user/admin/comments/filter-values/')
      ]);

      setAllFilterValues({
        users: {
          usernames: usersRes.data.usernames,
          emails: usersRes.data.emails
        },
        articles: {
          titles: articlesRes.data.titles,
          sources: articlesRes.data.sources
        },
        summaries: {
          articleTitles: summariesRes.data.article_titles
        },
        comments: {
          usernames: commentsRes.data.usernames,
          articleTitles: commentsRes.data.article_titles
        }
      });

      // Cập nhật filters cho các cột
      userColumns[0].filters = usersRes.data.usernames.map(username => ({ text: username, value: username }));
      userColumns[1].filters = usersRes.data.emails.map(email => ({ text: email, value: email }));
      
      articleColumns[0].filters = articlesRes.data.titles.map(title => ({ text: title, value: title }));
      articleColumns[1].filters = articlesRes.data.sources.map(source => ({ text: source, value: source }));
      
      summaryColumns[0].filters = summariesRes.data.article_titles.map(title => ({ text: title, value: title }));
      
      commentColumns[1].filters = commentsRes.data.usernames.map(username => ({ text: username, value: username }));
      commentColumns[2].filters = commentsRes.data.article_titles.map(title => ({ text: title, value: title }));

    } catch (error) {
      console.error('Error fetching filter values:', error);
      message.error('Lỗi khi tải dữ liệu filter');
    }
  };

  // Gọi fetchAllFilterValues khi component mount và khi chuyển tab
  useEffect(() => {
    fetchAllFilterValues();
  }, [selectedMenu]);

  const renderContent = () => {
    // Tạo showTotal function ở đây thay vì lưu trong state
    const showTotal = (total, range) => `${range[0]}-${range[1]} của ${total} mục`;
    
    switch (selectedMenu) {
      case 'dashboard':
        return (
          <>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Tổng số người dùng"
                    value={stats?.system_stats?.total_users}
                    loading={loading}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Tổng số bài viết"
                    value={stats?.system_stats?.total_articles}
                    loading={loading}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Tổng số tóm tắt"
                    value={stats?.system_stats?.total_summaries}
                    loading={loading}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Tổng số lượt xem"
                    value={stats?.system_stats?.total_views}
                    loading={loading}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card title="Thống kê tương tác">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Statistic
                        title="Tổng số bình luận"
                        value={stats?.system_stats?.total_comments}
                        loading={loading}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Người dùng mới (24h)"
                        value={stats?.system_stats?.new_users_24h}
                        loading={loading}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Bài viết mới (24h)"
                        value={stats?.system_stats?.new_articles_24h}
                        loading={loading}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Tóm tắt mới (24h)"
                        value={stats?.system_stats?.new_summaries_24h}
                        loading={loading}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Thống kê nguồn tin">
                  <Row gutter={[16, 16]}>
                    {stats?.source_stats?.map((source, index) => (
                      <Col span={12} key={index}>
                        <Statistic
                          title={source.source_name}
                          value={source.article_count}
                          loading={loading}
                          suffix={` bài viết`}
                        />
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">
                            {source.summary_count} tóm tắt
                          </Text>
                        </div>
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            Cập nhật: {new Date(source.last_scraped).toLocaleString('vi-VN')}
                          </Text>
                        </div>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card title="Crawl dữ liệu">
                  <Space>
                    <Button
                      type="primary"
                      icon={<SyncOutlined />}
                      onClick={() => handleCrawl('baomoi')}
                      style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
                    >
                      Crawl Báo Mới
                    </Button>
                    <Button
                      type="primary"
                      icon={<SyncOutlined />}
                      onClick={() => handleCrawl('vnexpress')}
                      style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
                    >
                      Crawl VnExpress
                    </Button>
                  </Space>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Tạo tóm tắt">
                  <Button
                    type="primary"
                    icon={<SyncOutlined />}
                    onClick={() => handleSummarize()}
                    style={{ backgroundColor: '#252525', color: 'white', borderColor: '#252525' }}
                  >
                    Tạo tóm tắt cho 10 bài viết tiếp theo
                  </Button>
                </Card>
              </Col>
            </Row>
          </>
        );
      case 'users':
        return (
          <Table
            columns={userColumns}
            dataSource={users}
            loading={loading}
            rowKey="id"
            pagination={{...pagination, showTotal}}
            onChange={handleTableChange}
          />
        );
      case 'articles':
        return (
          <Table
            columns={articleColumns}
            dataSource={articles}
            loading={loading}
            rowKey="id"
            pagination={{...pagination, showTotal}}
            onChange={handleTableChange}
          />
        );
      case 'summaries':
        if (selectedSummary) {
          const newsCardData = selectedArticle ? {
            id: selectedArticle.id,
            articleId: selectedArticle.article?.id,
            title: selectedArticle.article?.title || selectedSummary.article_title,
            summary: selectedArticle.summary_text,
            imageUrl: selectedArticle.article?.image_url,
            sourceUrl: selectedArticle.article?.url,
            keywords: selectedArticle.article?.keywords || [],
            publishedAt: selectedArticle.article?.published_at,
            userVote: null,
            upvotes: selectedArticle.upvotes,
            downvotes: selectedArticle.downvotes,
            isBookmarked: false
          } : {
            id: selectedSummary.id,
            articleId: selectedSummary.article_id,
            title: selectedSummary.article_title,
            summary: detailLoading ? '' : (detailError || 'Không có tóm tắt để hiển thị.'),
            imageUrl: null,
            sourceUrl: '#',
            keywords: [],
            publishedAt: null,
            userVote: null,
            upvotes: selectedSummary.upvotes,
            downvotes: selectedSummary.downvotes,
            isBookmarked: false
          };

          return (
            <div>
              <Button 
                type="text" 
                icon={<ArrowLeftOutlined />} 
                onClick={handleBackToList} 
                className="mb-4"
              >
                Quay lại danh sách
              </Button>
              <Row justify="center" style={{ paddingTop: '0', paddingBottom: '2rem' }}>
                <Col style={{ maxWidth: '600px', width: '100%' }}>
                  <Spin spinning={detailLoading} tip="Đang tải chi tiết..." size="large">
                    {(!detailLoading && (selectedArticle || detailError)) && (
                      <NewsCard
                        {...newsCardData}
                        showBookmarkButton={false}
                        showRating={false}
                        onBookmarkToggle={() => {}}
                        onHideArticle={handleBackToList}
                        showCommentButton={false}
                        showShareButton={false}
                      />
                    )}
                  </Spin>
                </Col>
              </Row>
            </div>
          );
        }
        return (
          <Table
            columns={summaryColumns}
            dataSource={summaries}
            loading={loading}
            rowKey="id"
            pagination={{...pagination, showTotal}}
            onChange={handleTableChange}
          />
        );
      case 'comments':
        return (
          <Table
            columns={commentColumns}
            dataSource={comments}
            loading={loading}
            rowKey="id"
            pagination={{...pagination, showTotal}}
            onChange={handleTableChange}
          />
        );
      case 'fav-words':
        if (selectedKeyword) {
          return (
            <div>
              <Button 
                type="text" 
                icon={<ArrowLeftOutlined />} 
                onClick={handleBackToKeywords} 
                className="mb-4"
              >
                Quay lại danh sách từ khóa
              </Button>
              <Card title={`Danh sách người dùng có từ khóa "${selectedKeyword}"`}>
                <Table
                  columns={keywordUsersColumns}
                  dataSource={keywordUsers}
                  loading={loading}
                  rowKey="id"
                  pagination={{...keywordUsersPagination, showTotal}}
                  onChange={handleKeywordUsersTableChange}
                />
              </Card>
            </div>
          );
        }
        return (
          <Table
            columns={favoriteWordsColumns}
            dataSource={favoriteWords}
            loading={loading}
            rowKey="keyword"
            pagination={{...pagination, showTotal}}
            onChange={handleTableChange}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        className="bg-white shadow-md"
        width={250}
        theme="light"
        breakpoint="lg"
        collapsedWidth={80}
        style={{
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          transition: 'width 0.2s ease-in-out',
          overflow: 'hidden',
        }}
      >
        <div className={`p-4 h-16 flex items-center ${collapsed ? 'justify-center' : ''}`}>
          <img
            src={logo}
            alt="Logo"
            className={`transition-all duration-300 max-w-full ${collapsed ? 'h-6 w-auto' : 'h-8 w-auto'}`}
            width={collapsed ? 80 : 250}
          />
        </div>

        <div className="flex flex-col flex-grow justify-between h-[calc(100vh-64px)]" style={{ marginLeft: '10px', marginRight: '10px' }}>
          <div className="flex flex-col">
            <Menu
              theme="light"
              mode="inline"
              selectedKeys={[selectedMenu]}
              onSelect={({ key }) => setSelectedMenu(key)}
              style={{
                borderRight: 0,
              }}
              items={[
                {
                  key: 'dashboard',
                  icon: <DashboardOutlined />,
                  label: 'Dashboard',
                },
                {
                  key: 'users',
                  icon: <UserOutlined />,
                  label: 'Quản lý người dùng',
                },
                {
                  key: 'articles',
                  icon: <FileTextOutlined />,
                  label: 'Quản lý bài viết',
                },
                {
                  key: 'summaries',
                  icon: <FileSearchOutlined />,
                  label: 'Quản lý tóm tắt',
                },
                {
                  key: 'comments',
                  icon: <CommentOutlined />,
                  label: 'Quản lý bình luận',
                },
                {
                  key: 'fav-words',
                  icon: <TagsOutlined />,
                  label: 'Quản lý từ khóa',
                },
              ]}
              className="admin-sidebar-menu"
            />
          </div>

          <div className="mb-4 px-4">
            <Button
              danger
              icon={<LogoutOutlined />}
              className="w-full flex items-center justify-center"
              style={{marginTop: '80px', marginLeft: '15px'}}
              onClick={handleLogout}
            >
              {!collapsed && "Logout"}
            </Button>
          </div>
        </div>
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'margin-left 0.2s' }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
        }}>
          <Title level={3} style={{ margin: 0 }}>Admin Dashboard</Title>
          <Button
            type="primary"
            icon={<LockOutlined />}
            onClick={() => setChangePasswordVisible(true)}
            style={{ backgroundColor: '#252525', borderColor: '#252525' }}
          >
            Đổi mật khẩu
          </Button>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          {renderContent()}
        </Content>
      </Layout>

      <ChangePasswordModal
        visible={changePasswordVisible}
        onClose={() => setChangePasswordVisible(false)}
      />
    </Layout>
  );
};

export default AdminDashboard;
