import type { APIContext } from 'astro';
import { getCategoryKeys, categories } from '@/lib/categories';
import { getCollection, type CollectionEntry } from 'astro:content';
import type { CategoryKey } from '@/lib/categories';

type Props = {
  post: CollectionEntry<'articles'> | CollectionEntry<'devlogs'> | CollectionEntry<'examples'>;
  category: CategoryKey;
};

export const getStaticPaths = async () => {
  const categoryKeys = getCategoryKeys().filter((key) => key !== 'examples');

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
    body: post.body ?? '',
  };

  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' },
  });
};
