import { getCollection } from 'astro:content';

export const categories = {
	articles: {
		collection: 'articles' as const,
		title: 'All Articles',
		label: 'Articles',
	},
	devlogs: {
		collection: 'devlogs' as const,
		title: 'All DevLogs',
		label: 'DevLogs',
	},
	examples: {
		collection: 'examples' as const,
		title: 'All Examples',
		label: 'Examples',
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
