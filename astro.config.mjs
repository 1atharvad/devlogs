// @ts-check

import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel';
import { defineConfig } from 'astro/config';
import path from "path";

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  site: 'https://blog.atharvadevasthali.com',
  output: 'static',
  adapter: vercel(),
  integrations: [mdx(), react()],
  vite: {
    resolve: {
      alias: {
        "@": path.resolve("./src"),
      },
    },
  },
});