import { SquareArrowOutUpRight } from 'lucide-react';
import type { ReactElement, FC, PropsWithChildren } from 'react';


export interface HeroLinkProps extends PropsWithChildren {
  href: string;
}

export function HeroLink({ href, children }: HeroLinkProps): ReactElement<FC> {
  return (
    <a href={href} target="_blank" className="text-blue-600 hover:text-blue-800 visited:text-blue-700 transition-colors">
      {children}
      <SquareArrowOutUpRight className="inline-block" size={14} />
    </a>
  );
}

export default function Hero(): ReactElement<FC> {
  return (
    <section className="grid grid-flow-row gap-4 pb-4">
      <h1 className="font-bold text-4xl">Social Media API Extractor</h1>
      <p>
        This application by <HeroLink href="https://cibmangotree.org">CIB Mango Tree</HeroLink> pulls datasets of social media activity from the Open Measures API.
        Under the free API, users are limited to social media data that is 6 months old or older.
        For more recent data, users can contact <HeroLink href="https://openmeasures.io">Open Measures</HeroLink> for competitive quotes on plans that provide recent data for a range of social media platforms.
        After extracting datasets from the API, users can analyze the data using the <HeroLink href="https://github.com/civictechdc/mango-tango-cli/tree/main">CIB Mango Tree application</HeroLink>.
      </p>
    </section>
  );
}
