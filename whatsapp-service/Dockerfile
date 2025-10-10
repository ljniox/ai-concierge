FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Create auth directory
RUN mkdir -p auth/gust-ia

# Expose port
EXPOSE 3001

# Start the service
CMD ["node", "index.js"]