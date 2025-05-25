import React from 'react'
import { Row, Col } from 'antd';
import NewsContent from '../components/NewsContent';
import { useSearchParams } from 'react-router-dom';
import { Typography } from 'antd';

const { Title } = Typography;

function Home() {
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('q');

  return (
    <Row justify="center" align="middle" style={{ minHeight: 'calc(100vh - 32px)' }}>
      <Col style={{ maxWidth: '600px', width: '100%' }}>
        {!searchQuery}
        <NewsContent fetchMode="recommendations" searchQuery={searchQuery} />
      </Col>
    </Row>
  )
}

export default Home
