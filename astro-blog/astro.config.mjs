import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

// 构建与开发服务器缓存分开，避免生产构建让运行中的 Vite 开发缓存失效。
const isProductionBuild = process.env.npm_lifecycle_event === 'build';

export default defineConfig({
  integrations: [
    vue(),
    tailwind({ applyBaseStyles: false }),
  ],
  prefetch: true,
  devToolbar: { enabled: false },
  adapter: node({ mode: 'standalone' }),
  server: {
    port: 4321,
  },
  vite: {
    cacheDir: isProductionBuild ? 'node_modules/.vite-build' : 'node_modules/.vite',
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:1235',
          changeOrigin: true,
          proxyTimeout: 600000,    // 10 分钟，长工具不会断
          timeout: 600000,
        },
        '/uploads': {
          target: 'http://localhost:1235',
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@layouts': '/src/layouts',
        '@lib': '/src/lib',
        '@styles': '/src/styles',
      },
    },
  },
});
