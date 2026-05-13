import { useEffect, useId, useRef } from 'react';

interface MermaidProps {
  chart: string;
  caption?: string;
}

export default function Mermaid({ chart, caption }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null);
  const rawId = useId();
  const id = rawId.replace(/:/g, '');

  useEffect(() => {
    import('mermaid').then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        themeVariables: {
          primaryColor: '#fff7ed',
          primaryTextColor: '#1c1917',
          primaryBorderColor: '#ea580c',
          lineColor: '#c2410c',
          secondaryColor: '#fef3c7',
          tertiaryColor: '#fafaf9',
          fontFamily: 'Rubik, sans-serif',
          fontSize: '14px',
          edgeLabelBackground: '#fff7ed',
          clusterBkg: '#fff7ed',
        },
      });

      if (ref.current) {
        mermaid.render(`mermaid-${id}`, chart).then(({ svg }) => {
          if (ref.current) ref.current.innerHTML = svg;
        });
      }
    });
  }, [chart, id]);

  return (
    <figure
      className="my-8 md:mx-10 rounded-2xl border border-orange-200 overflow-hidden shadow-sm"
      style={{
        backgroundColor: '#fffbf7',
        backgroundImage:
          'linear-gradient(rgba(234,88,12,0.08) 1px, transparent 1px), linear-gradient(to right, rgba(234,88,12,0.08) 1px, transparent 1px)',
        backgroundSize: '28px 28px',
      }}
    >
      <div ref={ref} className="flex justify-center overflow-x-auto px-6 pt-6 pb-4 [&>svg]:max-w-full [&>svg]:h-auto" />
      {caption && (
        <figcaption className="text-center text-sm text-zinc-400 font-rubik pb-4 tracking-wide">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}
