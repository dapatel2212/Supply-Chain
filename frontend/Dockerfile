FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm cache clean --force && \
    npm install --force 2>&1 | tail -5

COPY . .

# Accept build arguments
ARG REACT_APP_TOMTOM_KEY
ARG REACT_APP_API_URL

# Set environment variables for build
ENV REACT_APP_TOMTOM_KEY=$REACT_APP_TOMTOM_KEY
ENV REACT_APP_API_URL=$REACT_APP_API_URL

EXPOSE 3000

CMD ["npm", "start"]
