import type { APIContext } from 'astro';
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

import siteData from '@/content/site.json';
import { categories, getCategoryKeys, type CategoryKey } from '@/lib/categories';

export async function GET(context: APIContext) {
	const categoryKeys = getCategoryKeys().filter((key) => key !== 'examples');

	const allPosts = await Promise.all(
		categoryKeys.map(async (key: CategoryKey) => {
			const posts = await getCollection(categories[key].collection, ({ data }) => !data.draft);
			return posts.map((post) => ({
				title: post.data.title,
				description: post.data.description,
				pubDate: post.data.pubDate,
				link: `/${key}/${post.id}/`,
			}));
		})
	);

	const items = allPosts
		.flat()
		.sort((a, b) => b.pubDate.valueOf() - a.pubDate.valueOf());

	return rss({
		title: siteData.title,
		description: siteData.description,
		site: context.site!,
		items,
	});
}
