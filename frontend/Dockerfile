# Sử dụng Node.js image
FROM node:22

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép package.json và package-lock.json
COPY package*.json ./

# Cài đặt dependencies
RUN npm install && \
    npm install -D tailwindcss@latest postcss@latest autoprefixer@latest && \
    npm install react react-dom react-router-dom prop-types axios \
                react-infinite-scroll-component \
                antd @ant-design/icons \
                @reduxjs/toolkit react-redux && \
    npm install @tailwindcss/line-clamp

# Sao chép source code
COPY . .

# Thiết lập môi trường
ENV PATH="/app/node_modules/.bin:$PATH"
ENV VITE_HOST=0.0.0.0

# Mở cổng
EXPOSE 5173

# Chạy server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
