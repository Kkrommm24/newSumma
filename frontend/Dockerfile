# Use official Node.js image
FROM node:22

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the project
COPY . .

# Expose Vite port
EXPOSE 5173

# Start Vite dev server
CMD ["npm", "run", "dev"]
