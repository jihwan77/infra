# === Next.js 런타임 전용 이미지 ===
FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

ARG NEXT_PUBLIC_API_BASE
ARG NEXT_PUBLIC_LAMBDA_ANALYSIS_URL
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}
ENV NEXT_PUBLIC_LAMBDA_ANALYSIS_URL=${NEXT_PUBLIC_LAMBDA_ANALYSIS_URL}

# 1) root로 전환해서 ping 설치
USER root
RUN apk add --no-cache iputils curl libcap bind-tools \
    && setcap cap_net_raw+ep /bin/ping

# 2) 앱 파일 배치 및 의존성 설치
COPY package*.json ./
RUN npm ci --omit=dev

# ⬇⬇⬇ 여기 추가 (1)
COPY . .

# ⬇⬇⬇ 여기 추가 (2)
RUN npm run build

EXPOSE 3000

# 3) 다시 non-root로
USER node

CMD ["npm", "run", "start"]
