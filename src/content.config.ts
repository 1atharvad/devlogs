import { defineCollection, z, type SchemaContext } from 'astro:content';
import { glob } from 'astro/loaders';

const postSchema = ({ image }: SchemaContext) =>
	z.object({
		title: z.string(),
		description: z.string(),
		pubDate: z.coerce.date(),
		updatedDate: z.coerce.date().optional(),
		heroImage: image().optional(),
		heroImageAlt: z.string().optional(),
		examplePage: z.boolean().default(false),
		draft: z.boolean().default(false),
		tags: z.array(z.string()).default([]),
	});

const createCollection = (name: string) =>
	defineCollection({
		loader: glob({ base: `./src/content/${name}`, pattern: '**/*.{md,mdx}' }),
		schema: postSchema,
	});

const devlogs = createCollection('devlogs');
const articles = createCollection('articles');
const examples = createCollection('examples');

export const collections = { devlogs, articles, examples };
