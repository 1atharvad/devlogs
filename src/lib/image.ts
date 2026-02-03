import { getImage } from 'astro:assets';
import type { ImageMetadata } from 'astro';

interface ResponsiveImageOptions {
  widths?: number[];
  format?: 'webp' | 'avif' | 'png' | 'jpg';
  quality?: number;
}

interface ResponsiveImageResult {
  src: string;
  srcSet: string;
  width: number;
  height: number;
}

export const getResponsiveImage = async (
  image: ImageMetadata,
  options: ResponsiveImageOptions = {}
): Promise<ResponsiveImageResult> => {
  const {
    widths = [640, 960, 1280, 1920],
    format = 'webp',
    quality = 80,
  } = options;

  const validWidths = widths.filter(w => w <= image.width);
  if (image.width < Math.max(...widths) && !validWidths.includes(image.width)) {
    validWidths.push(image.width);
  }
  validWidths.sort((a, b) => a - b);

  const images = await Promise.all(
    validWidths.map(width => getImage({ src: image, width, format, quality }))
  );

  const srcSet = images.map((img, i) => `${img.src} ${validWidths[i]}w`).join(', ');
  const fallback = images[images.length - 1];

  return {
    src: fallback.src,
    srcSet,
    width: fallback.attributes.width as number,
    height: fallback.attributes.height as number,
  };
}
