# Stage 1: Build the Next.js application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install pnpm for potentially faster installs, if preferred
# RUN npm install -g pnpm

# Copy package.json and lock file
COPY package.json ./
# COPY pnpm-lock.yaml ./  # If using pnpm
COPY package-lock.json ./ 

# Install dependencies
# RUN pnpm install --frozen-lockfile # If using pnpm
RUN npm install

# Copy the rest of the application code
COPY . .

# Set build-time arguments if needed, e.g., for NEXT_PUBLIC_API_URL
# ARG NEXT_PUBLIC_API_URL
# ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the Next.js application
RUN npm run build

# Stage 2: Production image
FROM node:18-alpine

WORKDIR /app

# Set environment to production
ENV NODE_ENV production

# Copy built assets from the builder stage
# This includes the .next folder (standalone output) and public folder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static


# Expose the port Next.js runs on (default 3000)
EXPOSE 3000

# Set the user to run the application (optional, good practice)
# USER node # Next.js standalone output might require specific user or permissions.
# For simplicity, we'll run as root for now, but 'node' user is better for security if permissions allow.
# The standalone output is designed to be run by a non-root user.
# We need to ensure the user 'node' (default GID 65534, UID 65534 on alpine node) has permissions for copied files.
# The --chown=node:node in COPY helps with this.

# Command to run the Next.js application (using the standalone server.js)
# The standalone output typically has a server.js file in the .next/standalone directory.
# When copying, we copy the contents of .next/standalone to ./
CMD ["node", "server.js"]

# Note: For Next.js 12.2+ with `output: 'standalone'` in `next.config.js`,
# the build output in `.next/standalone` includes a minimal server and copies necessary node_modules.
# This Dockerfile assumes `output: 'standalone'` is configured or will be configured.
# If not, the approach would be different (copying .next, node_modules, package.json, and running `next start`).
# For now, I will proceed with the standalone assumption as it's best practice for Docker.
# I should add `output: 'standalone'` to `next.config.js`.
