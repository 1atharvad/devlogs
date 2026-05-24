import { getCollection } from 'astro:content';

export const categories = {
	devlogs: {
		collection: 'devlogs' as const,
		title: 'All DevLogs',
		label: 'DevLogs',
	},
	articles: {
		collection: 'articles' as const,
		title: 'All Articles',
		label: 'Articles',
	},
} as const;

export type CategoryKey = keyof typeof categories;

export const getCategoryPosts = async (category: CategoryKey) => {
	const config = categories[category];
	const posts = await getCollection(config.collection);
	return posts
		.filter(post => !post.data.draft)
		.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
};

export const getCategoryKeys = (): CategoryKey[] => {
	return Object.keys(categories) as CategoryKey[];
};
