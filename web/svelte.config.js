import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // Consult https://kit.svelte.dev/docs/integrations#preprocessors
  // for more information about preprocessors
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      // default options are suitable for this project
      // pages: 'build',
      // assets: 'build',
      // fallback: undefined, // can be 'index.html' or '200.html' or '404.html' if SPA mode
      // precompress: false,
      // strict: true
    })
  }
};

export default config;
