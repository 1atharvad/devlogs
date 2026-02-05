import { useState } from 'react';

interface Props {
  tags: string[];
}

export const TagFilter = ({ tags }: Props) => {
  const [activeTag, setActiveTag] = useState<string>('All');

  const filterPosts = (tag: string) => {
    setActiveTag(tag);

    const cards = document.querySelectorAll('.js-post-card');
    cards.forEach((card) => {
      const primaryTag = card.getAttribute('data-primary-tag') || '';
      if (tag === 'All' || primaryTag === tag) {
        (card as HTMLElement).style.display = '';
      } else {
        (card as HTMLElement).style.display = 'none';
      }
    });
  };

  return (
    <>
      {tags.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2.5 mt-10">
          {tags.map((tag) => (
            <button
              key={tag}
              className={`inline-flex items-center rounded-full font-rubik uppercase border px-4 py-1.5 text-sm font-normal transition-colors border-none outline outline-1 ${
                activeTag === tag
                  ? 'bg-orange-600 text-neutral-50 outline-orange-100'
                  : 'outline-zinc-600 text-zinc-600'
              }`}
              onClick={() => filterPosts(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
      )}
    </>
  );
};
