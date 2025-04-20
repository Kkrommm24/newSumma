import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"
import { ConfigProvider, App as AntApp } from 'antd';

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          fontFamily: '"Be Vietnam Pro", sans-serif',
          colorPrimary: '#101720',
        },
      }}
    >
      <AntApp>
        <App />
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>,
)
