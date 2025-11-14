import { Link } from '@tanstack/react-router';
import { Image } from '@unpic/react';
import { Button } from '@components/ui/button';
import type { ReactElement, FC } from 'react';

export default function Header(): ReactElement<FC> {
  return (
    <header className="grid grid-flow-col h-header-height w-full items-center justify-between bg-zinc-300 dark:bg-zinc-500 py-4 px-52">
      <div className="grid grid-flow-col items-center">
        <Link to="/">
          <Image
            src="/mango-text.PNG"
            width={64}
            height={64}
          />
        </Link>
        <h1 className="font-bold text-3xl">CIB Mango Tree</h1>
        <span className="font-light text-sm ml-4 mt-2">A Civic Tech DC Project</span>
      </div>
      <div className="grid grid-flow-col">
        <Button asChild>
          <a href="https://cibmangotree.org" target="_blank">Project Website</a>
        </Button>
      </div>
    </header>
  );
}
