import { useEffect, useState } from 'react';

import { YearDotNav } from 'advi-ui';

interface YearNavItem {
  year: number;
  months: number[];
}

interface Props {
  items: YearNavItem[];
}

export const FilteredYearDotNav = ({ items }: Props) => {
  const [filteredItems, setFilteredItems] = useState(items);

  useEffect(() => {
    const handler = (e: Event) => {
      const { visibleMonthIds } = (e as CustomEvent<{ visibleMonthIds: Set<string> }>).detail;
      setFilteredItems(
        items
          .map(({ year, months }) => ({
            year,
            months: months.filter(m => visibleMonthIds.has(`year-${year}-month-${m}`)),
          }))
          .filter(({ months }) => months.length > 0)
      );
    };

    window.addEventListener('tagfilter', handler);
    return () => window.removeEventListener('tagfilter', handler);
  }, [items]);

  return <YearDotNav items={filteredItems} />;
};
