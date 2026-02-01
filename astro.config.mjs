// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';
import path from "path";

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  site: 'https://blog.atharvadevasthali.com',
  integrations: [mdx(), sitemap(), react()],
  vite: {
    resolve: {
      alias: {
        "@": path.resolve("./src"),
      },
    },
  },
});