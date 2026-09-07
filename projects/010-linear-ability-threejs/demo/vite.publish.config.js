import { defineConfig } from 'vite';

// Publish the original, asset-free extension demos. Upstream FBX/HDR/textures
// stay in the local sandbox and are not redistributed by this static build.
export default defineConfig({
  base: './',
  publicDir: false,
  plugins: [{
    name: 'public-demo-navigation',
    transformIndexHtml(html) {
      return html
        .replace('href="./showcase.html"', 'href="./index.html"')
        .replace('href="./skills.html">原版七种技能 ↗', 'href="https://github.com/yydshly/0907_codex_project/tree/main/projects/010-linear-ability-threejs#原版技能">原版技能与运行说明 ↗');
    }
  }],
  build: {
    outDir: 'dist-publish',
    target: 'es2022',
    chunkSizeWarningLimit: 1000,
    rollupOptions: { input: 'showcase.html' }
  }
});
