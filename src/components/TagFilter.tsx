import { useState } from 'react';

import { Button } from 'advi-ui';

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

    const visibleMonthIds = new Set<string>();
    document.querySelectorAll('.js-month-group').forEach((group) => {
      const groupCards = group.querySelectorAll<HTMLElement>('.js-post-card');
      const hasVisible = Array.from(groupCards).some(c => c.style.display !== 'none');
      (group as HTMLElement).style.display = hasVisible ? '' : 'none';
      if (hasVisible) visibleMonthIds.add(group.id);
    });

    window.dispatchEvent(new CustomEvent('tagfilter', { detail: { visibleMonthIds } }));
  };

  return (
    <>
      {tags.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2.5 mt-10">
          {tags.map((tag) => (
            <Button
              key={tag}
              variant={activeTag === tag ? 'default' : 'outline'}
              size="sm"
              className={`rounded-full font-rubik uppercase text-sm font-normal ${
                activeTag === tag
                  ? '!bg-orange-600 hover:!bg-orange-700 !border-orange-600 !text-neutral-50'
                  : '!border-zinc-600 !text-zinc-600 hover:!bg-zinc-100'
              }`}
              onClick={() => filterPosts(tag)}
            >
              {tag}
            </Button>
          ))}
        </div>
      )}
    </>
  );
};
