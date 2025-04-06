import React from 'react'
import { Row, Col } from 'antd';
import NewsContent from '../components/NewsContent';

function Home() {
  return (
    <Row justify="center" align="middle" style={{ minHeight: 'calc(100vh - 32px)' }}>
      <Col style={{ maxWidth: '600px', width: '100%' }}>
        <NewsContent />
      </Col>
    </Row>
  )
}

export default Home
