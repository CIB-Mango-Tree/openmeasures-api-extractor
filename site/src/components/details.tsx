import { useMemo } from 'react';
import { format } from 'date-fns';
import { useSelectedQuery } from '@lib/state/query';
import { Sheet, FileJson2, FileSpreadsheet } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter, DialogHeader } from '@components/ui/dialog';
import { Button } from '@components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@components/ui/dropdown-menu';
import { Badge } from '@components/ui/badge';
import { Separator } from '@components/ui/separator';
import { QUERY_COMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { SelectedQueryState } from '@state/query';

export function QueryDetailsDialog(): ReactElement<FC> {
  const state = useSelectedQuery((state: SelectedQueryState): SelectedQueryState => state);
  const baseUrl = useMemo((): string => `${import.meta.env.VITE_API_URL}/api/queries/${state.selectedQuery?.id}/download`, [state.selectedQuery]);
  const completedPercentage = useMemo((): number => state.selectedQuery != null ? Math.round(state.selectedQuery?.percentage * 100) : 0, [state.selectedQuery]);
  const handleDialogClose = (): void => state.clear();

  return (
    <Dialog open={state.selectedQuery != null}>
      <DialogContent onInteractOutside={handleDialogClose} showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Extraction Details</DialogTitle>
          <DialogDescription className="capitalize">
            {state.selectedQuery?.platform}
          </DialogDescription>
        </DialogHeader>
        <Separator />
        <div className="grid grid-flow-row gap-y-2">
          <div className="grid grid-flow-col grid-cols-8">
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">Extraction Date</h3>
              <span className="text-sm text-muted-foreground">
                {state.selectedQuery != null ? format(new Date(state.selectedQuery.createdAt), 'yyy/MM/dd') : '-'}
              </span>
            </div>
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">Extraction Completion</h3>
              <span className="text-sm text-muted-foreground">
                {completedPercentage}%
              </span>
            </div>
          </div>
          <div className="grid grid-flow-col grid-cols-8">
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">Left to Complete</h3>
              <span className="text-sm text-muted-foreground">
                {100 - completedPercentage}%
              </span>
            </div>
          </div>
        </div>
        <Separator />
        <div className="grid grid-flow-row gap-y-2">
          <div className="grid grid-flow-col grid-cols-8">
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">Time Zone</h3>
              <span className="text-sm text-muted-foreground">
                {state.selectedQuery?.timezone}
              </span>
            </div>
          </div>
          <div className="grid grid-flow-col grid-cols-8">
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">From</h3>
              <span className="text-sm text-muted-foreground">
                {state.selectedQuery?.startDate != null ? format(new Date(state.selectedQuery?.startDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
              </span>
            </div>
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">To</h3>
              <span className="text-sm text-muted-foreground">
                {state.selectedQuery?.endDate != null ? format(new Date(state.selectedQuery?.endDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
              </span>
            </div>
          </div>
          <div className="grid grid-flow-col grid-cols-8">
            <div className="grid grid-flow-row col-span-4">
              <h3 className="font-medium text-sm">Social Media Platform</h3>
              <span className="text-sm text-muted-foreground">
                {state.selectedQuery?.platform}
              </span>
            </div>
          </div>
        </div>
        <Separator />
        <DialogFooter className="sm:justify-between">
          <Button
            variant="outline"
            className="cursor-pointer"
            onClick={handleDialogClose}>
            Close
          </Button>
          {state.selectedQuery?.status !== QUERY_COMPLETE && (
            <Button variant="default" className="cursor-pointer">Complete Extraction</Button>
          )}
          {state.selectedQuery?.status === QUERY_COMPLETE && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button className="cursor-pointer">
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <a className="inline-flex items-center" href={state.selectedQuery ? `${baseUrl}/csv` : ''}>
                    <FileSpreadsheet />
                    <span className="pl-1 font-bold">CSV</span>
                  </a>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <a className="inline-flex items-center" href={state.selectedQuery ? `${baseUrl}/excel` : ''}>
                    <Sheet />
                    <span className="pl-1 font-bold">EXCEL</span>
                  </a>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <a className="inline-flex items-center" href={state.selectedQuery ? `${baseUrl}/json` : ''}>
                    <FileJson2 />
                    <span className="pl-1 font-bold">JSON</span>
                  </a>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
