import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Force root index.html as the only build entry and split vendor chunks for better cache reuse.
export default defineConfig({
  plugins: [react()],
  build: {
    cssCodeSplit: true,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return;
          }
          if (id.includes('react') || id.includes('scheduler') || id.includes('react-router-dom')) {
            return 'react-vendor';
          }
          if (id.includes('antd') || id.includes('@ant-design/icons') || id.includes('/rc-')) {
            return 'antd-vendor';
          }
          return 'vendor';
        },
      },
    },
  },
});
