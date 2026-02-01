import { forwardRef } from 'react';
import "@/styles/components/image.scss";

type ImageSrc = string | { src: string };

interface ImageProps {
  src: ImageSrc;
  alt: string;
  className?: string;
  wrapperClassName?: string;
  lazyload?: boolean;
}

interface ImageWithCaptionProps extends ImageProps {
  caption?: string;
}

const resolveSrc = (src: ImageSrc): string =>
  typeof src === 'string' ? src : src.src;

export const Image = forwardRef<HTMLDivElement, ImageProps>(
  ({ src, alt, className = '', wrapperClassName = '', lazyload = false }, ref) => {
    const resolvedSrc = resolveSrc(src);
    const imgProps = lazyload ? { 'data-src': resolvedSrc } : { src: resolvedSrc };

    return (
      <div ref={ref} className={`image-wrapper ${wrapperClassName}`.trim()}>
        {lazyload && <div className="image-sizer" />}
        <img
          className={`image-frame ${className}`.trim()}
          {...imgProps}
          alt={alt}
        />
      </div>
    );
  }
);

Image.displayName = 'Image';

export const ImageWithCaption = forwardRef<HTMLElement, ImageWithCaptionProps>(
  ({ src, alt, className = '', caption, lazyload = false }, ref) => {
    const resolvedSrc = resolveSrc(src);
    const imgProps = lazyload ? { 'data-src': resolvedSrc } : { src: resolvedSrc };

    return (
      <figure ref={ref} className="image-wrapper">
        {lazyload && <div className="image-sizer" />}
        <img
          className={`image-frame ${className}`.trim()}
          {...imgProps}
          alt={alt}
        />
        {caption && (
          <figcaption className="image-caption">
            {caption}
          </figcaption>
        )}
      </figure>
    );
  }
);

ImageWithCaption.displayName = 'ImageWithCaption';