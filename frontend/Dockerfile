# ./frontend/Dockerfile
FROM node:22

WORKDIR /frontend

# först bara lock-filer – snabbare bygg
COPY package.json package-lock.json ./

# deterministiskt install + npm-workaround
RUN npm install --frozen-lockfile

# kopiera resten
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
