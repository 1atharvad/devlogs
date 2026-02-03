import { useEffect, useRef } from 'react';
import "@/styles/components/image.scss";

type ImageSrc = string | { src: string; width?: number; height?: number };

interface ImageProps {
  src: ImageSrc;
  alt: string;
  className?: string;
  wrapperClassName?: string;
  lazyload?: boolean;
  srcSet?: string;
  sizes?: string;
  width?: number;
  height?: number;
  decoding?: 'async' | 'sync' | 'auto';
  fetchPriority?: 'high' | 'low' | 'auto';
}

interface ImageWithCaptionProps extends ImageProps {
  caption?: string;
}

const resolveSrc = (src: ImageSrc): { src: string; width?: number; height?: number } => {
  if (typeof src === 'string') return { src };
  return { src: src.src, width: src.width, height: src.height };
};

export const Image = ({
  src,
  alt,
  className = '',
  wrapperClassName = '',
  lazyload = false,
  srcSet,
  sizes,
  width,
  height,
  decoding = 'async',
  fetchPriority,
}: ImageProps) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const resolved = resolveSrc(src);
  const imgWidth = width ?? resolved.width;
  const imgHeight = height ?? resolved.height;

  const imgProps = lazyload
    ? { 'data-src': resolved.src, 'data-srcset': srcSet }
    : { src: resolved.src, srcSet };

  useEffect(() => {
    if (!lazyload || !imageRef.current) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const targetEl = entry.target as HTMLImageElement;
          if (targetEl.dataset.srcset) targetEl.srcset = targetEl.dataset.srcset;
          if (targetEl.dataset.src) targetEl.src = targetEl.dataset.src;
          observer.disconnect();
        }
      });
    }, { rootMargin: '0px', threshold: 0.0 });

    observer.observe(imageRef.current);

    return () => observer.disconnect();
  }, [lazyload]);

  const aspectRatio = imgWidth && imgHeight ? (imgHeight / imgWidth) * 100 : undefined;
  const sizerStyle = aspectRatio ? { '--default-height': `${aspectRatio}%` } as React.CSSProperties : undefined;

  return (
    <div className={`image-wrapper ${wrapperClassName}`.trim()}>
      {lazyload && <div className="image-sizer" style={sizerStyle} />}
      <img
        ref={imageRef}
        className={`image-frame ${className}`.trim()}
        {...imgProps}
        alt={alt}
        sizes={sizes}
        width={imgWidth}
        height={imgHeight}
        decoding={decoding}
        fetchPriority={fetchPriority}
      />
    </div>
  );
}

export const ImageWithCaption = ({
  src,
  alt,
  className = '',
  caption,
  lazyload = false,
  srcSet,
  sizes,
  width,
  height,
  decoding = 'async',
  fetchPriority,
}: ImageWithCaptionProps) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const resolved = resolveSrc(src);
  const imgWidth = width ?? resolved.width;
  const imgHeight = height ?? resolved.height;

  const imgProps = lazyload
    ? { 'data-src': resolved.src, 'data-srcset': srcSet }
    : { src: resolved.src, srcSet };

  useEffect(() => {
    if (!lazyload || !imageRef.current) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const targetEl = entry.target as HTMLImageElement;
          if (targetEl.dataset.srcset) targetEl.srcset = targetEl.dataset.srcset;
          if (targetEl.dataset.src) targetEl.src = targetEl.dataset.src;
          observer.disconnect();
        }
      });
    }, { rootMargin: '0px', threshold: 0.0 });

    observer.observe(imageRef.current);

    return () => observer.disconnect();
  }, [lazyload]);

  const aspectRatio = imgWidth && imgHeight ? (imgHeight / imgWidth) * 100 : undefined;
  const sizerStyle = aspectRatio ? { '--default-height': `${aspectRatio}%` } as React.CSSProperties : undefined;

  return (
    <figure className="image-wrapper">
      {lazyload && <div className="image-sizer" style={sizerStyle} />}
      <img
        ref={imageRef}
        className={`image-frame ${className}`.trim()}
        {...imgProps}
        alt={alt}
        sizes={sizes}
        width={imgWidth}
        height={imgHeight}
        decoding={decoding}
        fetchPriority={fetchPriority}
      />
      {caption && (
        <figcaption className="image-caption">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}
