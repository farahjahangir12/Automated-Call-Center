# Build React frontend
FROM node:20

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy all frontend code
COPY . .

# Build the app
RUN npm run build

# Install serve to run production build
RUN npm install -g serve

# Expose port 3000 (or the port you want)
EXPOSE 3000

# Start the app
CMD ["serve", "-s", "build", "-l", "3000"]
