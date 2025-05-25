import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.jsx"
import "./index.css"
import { ConfigProvider, App as AntApp } from 'antd';
import { Provider } from 'react-redux';
import { store } from './store';
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          fontFamily: '"Be Vietnam Pro", sans-serif',
          colorPrimary: '#101720',
        },
        components: {
          Message: {
            zIndexPopup: 1000,
          },
        },
      }}
    >
      <Provider store={store}>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <AntApp message={{ maxCount: 3 }}>
          <App />
        </AntApp>
        </BrowserRouter>
      </Provider>
    </ConfigProvider>
  </React.StrictMode>,
)
