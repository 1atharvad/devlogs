import { useRef, type ReactNode } from 'react';

import { gsap, useGSAP, ScrollTrigger } from '@/lib/gsap';

interface BannerProps {
  children: ReactNode;
  headline: string;
  tagline: string;
}

export const Banner = ({ children, headline, tagline }: BannerProps) => {
  const boxRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const createTimeline = () => {
      if (!boxRef.current) return;
      const timeline = gsap.timeline({
        scrollTrigger: {
          trigger: boxRef.current,
          start: 'top top',
          end: 'bottom top+=50%',
          scrub: true,
        },
      });

      timeline.to(boxRef.current, {
        borderRadius: '0.5rem',
        width: '90vw',
      });
    };

    let ctx = gsap.context(createTimeline, boxRef);

    const handleResize = () => {
      ctx.revert();
      ScrollTrigger.refresh();
      ctx = gsap.context(createTimeline, boxRef);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      ctx.revert();
    };
  }, { scope: boxRef });

  return (
    <section ref={boxRef} className="relative overflow-hidden left-1/2 -translate-x-1/2 h-[90vh] before:content-[''] before:absolute before:inset-0 before:bg-black/50 before:z-10">
      <div className="absolute w-full h-full">
        {children}
      </div>
      <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center text-white px-4">
        <h1 className="font-stack text-5xl md:text-8xl/tight font-bold mb-4 text-white">
          {headline}
        </h1>
        <p className="font-rubik text-lg md:text-xl max-w-2xl text-white/90">
          {tagline}
        </p>
      </div>
    </section>
  );
}