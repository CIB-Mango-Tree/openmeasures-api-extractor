import { useMemo } from 'react';
import { format } from 'date-fns';
import { useSelectedQuery } from '@lib/state/query';
import { cn } from '@lib/utils';
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter, DialogHeader } from '@components/ui/dialog';
import { Button } from '@components/ui/button';
import { Progress } from '@components/ui/progress';
import { Spinner } from '@components/ui/spinner';
import { Badge } from '@components/ui/badge';
import { Separator } from '@components/ui/separator';
import { ExportButton } from '@components/export';
import { QUERY_COMPLETE, FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { SelectedQueryState, CurrentViewType } from '@state/query';
import type { Query } from '@appTypes/query';

export function QueryDetailsHeader(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
  const currentView = useSelectedQuery((state: SelectedQueryState): CurrentViewType => state.currentView);
  const badgeClasses: string = cn({
    'bg-green-600/10 text-green-600': selectedQuery?.status === QUERY_COMPLETE,
    'bg-red-600/10 text-red-600': (
      selectedQuery?.status === FETCH_INCOMPLETE || selectedQuery?.status === CLEAN_INCOMPLETE ||
      selectedQuery?.status === PARSE_INCOMPLETE
    ),
    'bg-zinc-600/10 text-zinc-600': (
      selectedQuery?.status !== QUERY_COMPLETE && selectedQuery?.status !== FETCH_INCOMPLETE && selectedQuery?.status !== CLEAN_INCOMPLETE &&
      selectedQuery?.status !== PARSE_INCOMPLETE
    ),
  }, 'min-w-5 h-5 border-0 rounded-full font-bold tabular-nums ml-2');

  if (currentView === 'progress') return (
    <DialogHeader>
      <DialogTitle>Resuming Extraction</DialogTitle>
      <DialogDescription>
        Resuming the data extraction for {selectedQuery?.platform}
      </DialogDescription>
    </DialogHeader>
  );

  if (currentView === 'complete') return (
    <DialogHeader>
      <DialogTitle>Extraction Complete</DialogTitle>
      <DialogDescription>
        {selectedQuery?.platform}
      </DialogDescription>
    </DialogHeader>
  );

  return (
    <DialogHeader>
      <DialogTitle>Extraction Details</DialogTitle>
      <DialogDescription className="capitalize">
        {selectedQuery?.platform}
        <Badge className={badgeClasses}>{selectedQuery?.status}</Badge>
      </DialogDescription>
    </DialogHeader>
  );
}

export function QueryDetailsFooter(): ReactElement<FC> {
  const state = useSelectedQuery((state: SelectedQueryState): SelectedQueryState => state);
  const baseUrl = useMemo((): string => `${import.meta.env.VITE_API_URL}/api/queries/${state.selectedQuery?.id}/download`, [state.selectedQuery]);
  const handleClose = (): void => {
    if (state.currentView === 'complete') {
      state.clear();
      return;
    }

    state.removeQuery();
  };

  return (
    <DialogFooter className="sm:justify-between">
      <Button
        variant="outline"
        className="cursor-pointer"
        disabled={state.currentView === 'progress'}
        onClick={handleClose}>
        Close
      </Button>
      {state.selectedQuery?.status !== QUERY_COMPLETE && (
        <Button variant="default" className="cursor-pointer">Complete Extraction</Button>
      )}
      {state.selectedQuery?.status === QUERY_COMPLETE && <ExportButton id={state.selectedQuery.id} />}
    </DialogFooter>
  );
}

export function QueryDetails(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
  const completedPercentage = useMemo((): number => selectedQuery != null ? Math.round(selectedQuery?.percentage * 100) : 0, [selectedQuery]);

  return (
    <>
      <div className="grid grid-flow-row gap-y-2">
        <div className="grid grid-flow-col grid-cols-8">
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">Extraction Date</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery != null ? format(new Date(selectedQuery.createdAt), 'yyy/MM/dd') : '-'}
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
              {selectedQuery?.timezone}
            </span>
          </div>
        </div>
        <div className="grid grid-flow-col grid-cols-8">
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">From</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery?.startDate != null ? format(new Date(selectedQuery?.startDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
            </span>
          </div>
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">To</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery?.endDate != null ? format(new Date(selectedQuery?.endDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
            </span>
          </div>
        </div>
        <div className="grid grid-flow-col grid-cols-8">
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">Social Media Platform</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery?.platform}
            </span>
          </div>
        </div>
      </div>
    </>
  );
}

export function QueryDetailsProgress(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
  const progressPercentage: number = selectedQuery != null ? Math.round(selectedQuery.percentage * 100) : 0;

  return (
    <div className="grid grid-flow-row gap-y-2">
      <Spinner />
      <span>We are preparing your file...</span>
      <div className="grid-flow-col">
        <Progress value={progressPercentage} />
        <span>{progressPercentage}%</span>
      </div>
    </div>
  );
}

export function QueryDetailsCompletion(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
  const progressPercentage: number = selectedQuery != null ? Math.round(selectedQuery.percentage * 100) : 0;

  return (
    <div className="grid grid-flow-row gap-y-2">
      <div className="grid grid-flow-row">
        <h3 className="font-medium text-sm">Extraction Completion</h3>
        <span className="text-sm text-muted-foreground">{progressPercentage}%</span>
      </div>
      <div className="grid grid-flow-row">
        <h3 className="font-medium text-sm">Requests Used</h3>
        <span className="text-sm text-muted-foreground">-</span>
      </div>
    </div>
  );
}

export function QueryDetailsDialog(): ReactElement<FC> {
  const state = useSelectedQuery((state: SelectedQueryState): SelectedQueryState => state);
  const handleDialogClose = (): void => {
    if (state.currentView === 'details') state.removeQuery();
    if (state.currentView === 'complete') state.clear();
  };

  return (
    <Dialog open={state.selectedQuery != null}>
      <DialogContent onInteractOutside={handleDialogClose} showCloseButton={false}>
        <QueryDetailsHeader />
        <Separator />
        {state.currentView === 'details' && <QueryDetails />}
        {state.currentView === 'progress' && <QueryDetailsProgress />}
        {state.currentView === 'complete' && <QueryDetailsCompletion />}
        {state.currentView !== 'progress' && <Separator />}
        <QueryDetailsFooter />
      </DialogContent>
    </Dialog>
  );
}
