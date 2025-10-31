import { useState } from 'react';
import { cn } from '@lib/utils';
import { Sheet, FileJson2, FileSpreadsheet, ChevronDown } from 'lucide-react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@components/ui/dropdown-menu';
import { Button } from '@components/ui/button';
import type { ReactElement, FC } from 'react';

export interface ExportButtonProps {
  id?: string;
  disabled?: boolean;
}

export function ExportButton({ id, disabled = false }: ExportButtonProps): ReactElement<FC> {
  const [open, setOpen] = useState<boolean>(false);
  const baseUrl: string = `${import.meta.env.VITE_API_URL}/api/queries/${id}/download`;
  const chevronClasses: string = cn({ 'rotate-180': open }, 'transform-gpu transition-transform');
  const handleOpenChange = (open: boolean): void => setOpen(open);

  return (
    <DropdownMenu onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger asChild>
        <Button
          disabled={disabled}
          className="cursor-pointer">
          Export
          <ChevronDown className={chevronClasses} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem>
          <a className="inline-flex items-center" href={id != null ? `${baseUrl}/csv` : ''}>
            <FileSpreadsheet />
            <span className="pl-1 font-bold">CSV</span>
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <a className="inline-flex items-center" href={id != null ? `${baseUrl}/excel` : ''}>
            <Sheet />
            <span className="pl-1 font-bold">EXCEL</span>
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <a className="inline-flex items-center" href={id != null ? `${baseUrl}/json` : ''}>
            <FileJson2 />
            <span className="pl-1 font-bold">JSON</span>
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
