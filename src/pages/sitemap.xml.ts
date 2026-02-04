import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

const site = 'https://blog.atharvadevasthali.com';

export const GET: APIRoute = async () => {
  const categories = ['devlogs', 'articles'] as const;

  const allPosts = await Promise.all(
    categories.map(async (category) => {
      const posts = await getCollection(category, ({ data }) => !data.draft && !data.examplePage);
      return posts.map((post) => ({
        url: `${site}/${category}/${post.id}`,
        lastmod: post.data.updatedDate?.toISOString() ?? post.data.pubDate.toISOString(),
      }));
    })
  );

  const posts = allPosts.flat();

  const staticPages = [
    { url: site, lastmod: new Date().toISOString() },
    ...categories.map((cat) => ({ url: `${site}/${cat}`, lastmod: new Date().toISOString() })),
  ];

  const allUrls = [...staticPages, ...posts];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls.map(({ url, lastmod }) => `  <url>
    <loc>${url}</loc>
    <lastmod>${lastmod}</lastmod>
  </url>`).join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
