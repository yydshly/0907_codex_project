import { defineConfig } from 'vite';
export default defineConfig({base:'./',server:{host:'127.0.0.1',port:5190},build:{target:'es2022',chunkSizeWarningLimit:2000,rollupOptions:{input:{original:'index.html',showcase:'showcase.html',skills:'skills.html'}}}});
