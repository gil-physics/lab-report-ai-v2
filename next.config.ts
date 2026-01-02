import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    // 로컬 개발 환경에서만 Python 서버로 프록시
    // Vercel 배포 시에는 serverless function을 직접 사용
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/analyze',
          destination: 'http://localhost:8000/api/analyze',
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
