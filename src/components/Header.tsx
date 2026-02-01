import { cva, type VariantProps } from 'class-variance-authority';
import { twMerge } from 'tailwind-merge';
import clsx from 'clsx';
import { SITE_TITLE } from '@/consts';

import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import ScrollTrigger from 'gsap/ScrollTrigger';
import { useRef } from 'react';

gsap.registerPlugin(useGSAP, ScrollTrigger);

const headerVariants = cva(
  'fixed w-full z-[99999] m-0 px-4 flex min-h-16 shadow-soft',
  {
    variants: {
      variant: {
        default: 'bg-[#0F0F10]',
        animating: 'bg-transparent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

type HeaderVariants = VariantProps<typeof headerVariants>;

type HeaderProps = HeaderVariants & {
  className?: string;
}

export const Header = ({ variant = 'default', className = '' }: HeaderProps) => {
  const boxRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (variant !== 'animating') return;

    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: triggerRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      },
    });

    timeline.to(boxRef.current, {
      backgroundColor: '#0F0F10',
    });

    const handleResize = () => {
      gsap.set(boxRef.current, { clearProps: 'all' });
      ScrollTrigger.refresh();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      timeline.scrollTrigger?.kill();
      timeline.kill();
    };
  }, {
    scope: triggerRef,
    dependencies: [variant],
  });

  return (
    <>
      <header ref={boxRef} className={twMerge(
        clsx(headerVariants({ variant })),
        className
      )}>
        <nav className='flex items-center align-middle justify-between'>
          <h2 className='font-slackey m-0 text-2xl w-fit'>
            <a className='text-orange-200 text-shadow-soft' href='/'>
              {SITE_TITLE}
            </a>
          </h2>
        </nav>
      </header>
      <div ref={triggerRef} className='absolute h-[64px]'></div>
      {variant === 'default' && <div className='h-[64px]'></div>}
    </>
  );
};
