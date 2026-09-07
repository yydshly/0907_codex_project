import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  plugins: [{
    name: 'public-demo-navigation',
    transformIndexHtml(html, context) {
      html = html.replace('href="./showcase.html"', 'href="./index.html"');
      if (context.filename.endsWith('skills.html')) {
        html = html.replaceAll('href="./index.html" target="_blank"', 'href="./original.html" target="_blank"')
          .replace('src="./index.html"', 'src="./original.html"');
      }
      return html;
    }
  }],
  build: {
    outDir: 'dist-publish',
    target: 'es2022',
    chunkSizeWarningLimit: 2000,
    rollupOptions: { input: { original: 'index.html', showcase: 'showcase.html', skills: 'skills.html' } }
  }
});
