import { Link } from '@tanstack/react-router';
import { Image } from '@unpic/react';
import { Button } from '@components/ui/button';
import type { ReactElement, FC } from 'react';

export default function Header(): ReactElement<FC> {
  return (
    <header className="grid grid-flow-col h-header-height w-full items-center justify-between bg-zinc-400 px-20">
      <div className="grid grid-flow-row">
        <Link to="/">
          <Image
            src="https://cibmangotree.org/assets/images/mango-text.PNG"
            width={100}
            height={100}
          />
        </Link>
        <h1 className="">CIB Mango Tree</h1>
        <span>A Civic Tech DC Project</span>
      </div>
      <div className="grid grid-flow-col">
        <Button asChild>
          <a href="https://cibmangotree.org">Project Website</a>
        </Button>
      </div>
    </header>
  );
}
