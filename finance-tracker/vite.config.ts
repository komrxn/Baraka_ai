import * as process from 'node:process';
import { fileURLToPath, URL } from 'node:url';
import vue from '@vitejs/plugin-vue';
import { defineConfig, loadEnv } from 'vite';
// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    base: process.env.BASE_URL || '/',
    plugins: [
      vue(),
      {
        name: 'token-mw',
        configureServer(server) {
          server.middlewares.use('/token', async (req, res) => {
            try {
              const response = await fetch(`${env.VITE_API_URL}/api/account/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  userName: env.VITE_API_USER,
                  password: env.VITE_API_PASSWORD,
                }),
              });
              const result = await response.json();
              res.setHeader('Content-Type', 'application/json');
              res.setHeader('Set-Cookie', [`token=${result.token}; Path=/; SameSite=Strict`]);
              res.end(JSON.stringify({ success: true }));
            }

            catch (e) {
              res.statusCode = 500;
              res.end(JSON.stringify({ success: false }));
            }
          });
        },
      },
    ],

    server: {
      open: true,
      port: 1234,
      strictPort: true,
      hmr: {
        host: 'localhost',
        port: 1234,
      },
      proxy: {
        /*
        '/soliq': {
          target: 'https://my3.soliq.uz/',
          changeOrigin: true,
          rewrite: path => path.replace(/^\/soliq/, '/api/'),
        },
        */
      },
    },

    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
          additionalData: '@use "@/styles/responsive.scss" as *;',
        },
      },
    },

    resolve: {
      alias: [
        { find: '@', replacement: fileURLToPath(new URL('./src', import.meta.url)) },
      ],
    },
  };
});
