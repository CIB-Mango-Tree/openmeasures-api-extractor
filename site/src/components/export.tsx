import { useState } from 'react';
import { toast } from 'sonner';
import { cn } from '@lib/utils';
import { saveExport } from '@lib/download';
import { Sheet, FileJson2, FileSpreadsheet, ChevronDown } from 'lucide-react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@components/ui/dropdown-menu';
import { Button } from '@components/ui/button';
import { Spinner } from '@components/ui/spinner';
import type { ReactElement, FC } from 'react';
import type { ExportFormat } from '@lib/download';

export interface ExportButtonProps {
  id?: string;
  disabled?: boolean;
}

type FormatOption = { format: ExportFormat; label: string; icon: ReactElement<FC>; };

const FORMATS: Array<FormatOption> = [
  { format: 'csv', label: 'CSV', icon: <FileSpreadsheet /> },
  { format: 'excel', label: 'EXCEL', icon: <Sheet /> },
  { format: 'json', label: 'JSON', icon: <FileJson2 /> },
];

/**
 * Downloads an already-parsed query.
 *
 * Nothing here waits on the backend: the caller keeps this disabled until the query reports
 * COMPLETE, which arrives over the WebSocket. A partial extraction becomes exportable the same
 * way -- something asks the backend to parse what was fetched, and this enables when it lands.
 */
export function ExportButton({ id, disabled = false }: ExportButtonProps): ReactElement<FC> {
  const [open, setOpen] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const chevronClasses: string = cn({ 'rotate-180': open }, 'transform-gpu transition-transform');

  // Not an <a href>: inside the desktop webview a link to the download endpoint renders the file
  // in the window instead of saving it.
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
      console.error('an error occurred when saving the export', error);
      toast.error('Export failed', { description: 'Something went wrong saving the file.' });

    } finally {
      setSaving(false);
    }
  };

  return (
    <DropdownMenu onOpenChange={(open: boolean): void => setOpen(open)}>
      <DropdownMenuTrigger render={<Button
          disabled={disabled || saving}
          className="cursor-pointer">
          {saving && <Spinner />}
          Export
          <ChevronDown className={chevronClasses} />
        </Button>} />
      <DropdownMenuContent align="end">
        {FORMATS.map(({ format, label, icon }: FormatOption): ReactElement<FC> => (
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
