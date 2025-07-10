# Stage 1: Build the frontend application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
# SvelteKit with vite build. Output is assumed to be in 'build/' or '.svelte-kit/output/client/'
# We will try to copy from 'build' first, then from '.svelte-kit/output/prerendered' and '.svelte-kit/output/client'
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration (will be created in a later step)
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from the builder stage
# SvelteKit with adapter-auto typically outputs to .svelte-kit/output/
# Prerendered pages are in .svelte-kit/output/prerendered
# Client-side assets (JS, CSS) are in .svelte-kit/output/client/_app/
# Let's copy the relevant parts.
# Nginx root will be /usr/share/nginx/html
# With adapter-static, all output is typically in the 'build' directory.
# Copy the entire contents of the 'build' directory to nginx's web root.
COPY --from=builder /app/build/ /usr/share/nginx/html


# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
