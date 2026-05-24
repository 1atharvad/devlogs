import type { APIContext } from 'astro';
import { getCategoryKeys, categories } from '@/lib/categories';
import { getCollection, type CollectionEntry } from 'astro:content';
import type { CategoryKey } from '@/lib/categories';

type Props = {
  post: CollectionEntry<'articles'> | CollectionEntry<'devlogs'>;
  category: CategoryKey;
};

export const getStaticPaths = async () => {
  const categoryKeys = getCategoryKeys();

  const allPosts = await Promise.all(
    categoryKeys.map(async (key: CategoryKey) => {
      const posts = await getCollection(categories[key].collection, ({ data }) => !data.draft);
      return posts.map((post) => ({ post, category: key }));
    })
  );

  return allPosts.flat().map(({ post, category }) => ({
    params: { id: post.id },
    props: { post, category } as Props,
  }));
};

function cleanBody(raw: string): string {
  return raw
    .replace(/^import\s+.+$/gm, '')       // remove import statements
    .replace(/<[A-Z]\w*[\s\S]*?\/>/g, '') // remove self-closing JSX components
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export const GET = async ({ props, site }: APIContext<Props>) => {
  const { post, category } = props;

  const data = {
    id: post.id,
    category,
    url: `${site}${category}/${post.id}/`,
    title: post.data.title,
    description: post.data.description,
    pubDate: post.data.pubDate.toISOString(),
    updatedDate: post.data.updatedDate?.toISOString() ?? null,
    primaryTag: post.data.primaryTag ?? null,
    tags: post.data.tags,
    body: cleanBody(post.body ?? ''),
  };

  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' },
  });
};
