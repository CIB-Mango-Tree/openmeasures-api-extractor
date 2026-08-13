import { useState } from 'react';
import { toast } from 'sonner';
import { cn } from '@lib/utils';
import { saveExport } from '@lib/download';
import { Sheet, FileJson2, FileSpreadsheet, ChevronDown } from 'lucide-react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@components/ui/dropdown-menu';
import { Button } from '@components/ui/button';
import type { ReactElement, FC } from 'react';
import type { ExportFormat } from '@lib/download';

export interface ExportButtonProps {
  id?: string;
  disabled?: boolean;
}

const FORMATS: Array<{ format: ExportFormat; label: string; icon: ReactElement<FC>; }> = [
  { format: 'csv', label: 'CSV', icon: <FileSpreadsheet /> },
  { format: 'excel', label: 'EXCEL', icon: <Sheet /> },
  { format: 'json', label: 'JSON', icon: <FileJson2 /> },
];

export function ExportButton({ id, disabled = false }: ExportButtonProps): ReactElement<FC> {
  const [open, setOpen] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const chevronClasses: string = cn({ 'rotate-180': open }, 'transform-gpu transition-transform');
  const handleOpenChange = (open: boolean): void => setOpen(open);

  // Not an <a href> any more: inside the desktop webview a link to the download endpoint just
  // renders the file in the window, because there is no download manager to catch it.
  const handleExport = async (format: ExportFormat): Promise<void> => {
    if (id == null) return;

    setSaving(true);

    try {
      const result = await saveExport(id, format);

      if (result.status === 'error') {
        toast.error('Export failed', { description: result.message });
        return;
      }

      if (result.status === 'saved' && result.path != null) {
        toast.success('Export saved', { description: result.path });
      }

    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Export failed', { description: 'Something went wrong saving the file.' });

    } finally {
      setSaving(false);
    }
  };

  return (
    <DropdownMenu onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger render={<Button
          disabled={disabled || saving}
          className="cursor-pointer">
          Export
          <ChevronDown className={chevronClasses} />
        </Button>} />
      <DropdownMenuContent align="end">
        {FORMATS.map(({ format, label, icon }): ReactElement<FC> => (
          <DropdownMenuItem
            key={format}
            className="cursor-pointer"
            onClick={(): void => {
              void handleExport(format);
            }}>
            <span className="inline-flex items-center w-full">
              {icon}
              <span className="pl-1 font-bold">{label}</span>
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
