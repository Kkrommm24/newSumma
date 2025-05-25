import React, { useState, useEffect } from 'react';
import { FloatButton } from 'antd';
import { VerticalAlignTopOutlined, ReloadOutlined } from '@ant-design/icons';

const ScrollToTop = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setVisible(window.pageYOffset > 300);
    };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const reloadPage = () => {
    window.location.reload();
  };

  return (
    <div className="scroll-to-top-container">
      <FloatButton.Group
        trigger="hover"
        type="primary"
        style={{ right: 24, bottom: 24 }}
        className="custom-float-button"
      >
        <FloatButton
          icon={<VerticalAlignTopOutlined />}
          onClick={scrollToTop}
          tooltip="Lên đầu trang"
          style={{ backgroundColor: '#1f2937', color: 'white' }}
        />
        <FloatButton
          icon={<ReloadOutlined />}
          onClick={reloadPage}
          tooltip="Tải lại trang"
          style={{ backgroundColor: '#1f2937', color: 'white' }}
        />
      </FloatButton.Group>
    </div>
  );
};

export default ScrollToTop; 