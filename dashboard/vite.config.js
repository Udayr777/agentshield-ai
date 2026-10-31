import {defineConfig} from 'vite';
export default defineConfig({server:{proxy:{'/api':{target:process.env.GATEWAY_URL||'http://127.0.0.1:8080',changeOrigin:false}}}});
