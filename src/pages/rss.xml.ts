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
			return posts.map((post) => {
				const tags = [...new Set([...(post.data.primaryTag ? [post.data.primaryTag] : []), ...post.data.tags])];
				return {
					title: post.data.title,
					description: post.data.description,
					pubDate: post.data.pubDate,
					link: `/${key}/${post.id}/`,
					...(tags.length > 0 && { categories: tags }),
					...(post.data.updatedDate && { customData: `<atom:updated>${post.data.updatedDate.toISOString()}</atom:updated>` }),
				};
			});
		})
	);

	const allPostsFlat = allPosts.flat();

	const items = allPostsFlat.sort((a, b) => b.pubDate.valueOf() - a.pubDate.valueOf());

	const lastBuildDate = new Date(
		Math.max(...allPostsFlat.map((post) => {
			const updated = post.customData?.match(/atom:updated>([^<]+)/)?.[1];
			return updated ? Math.max(post.pubDate.valueOf(), new Date(updated).valueOf()) : post.pubDate.valueOf();
		}))
	);

	return rss({
		title: siteData.title,
		description: siteData.description,
		site: context.site!,
		xmlns: {
			atom: 'http://www.w3.org/2005/Atom',
			dc: 'http://purl.org/dc/elements/1.1/',
		},
		customData: [
			`<language>en-us</language>`,
			`<lastBuildDate>${lastBuildDate.toUTCString()}</lastBuildDate>`,
			`<atom:link href="${context.site!}rss.xml" rel="self" type="application/rss+xml"/>`,
			`<dc:creator>${siteData.author}</dc:creator>`,
		].join(''),
		items,
	});
}
