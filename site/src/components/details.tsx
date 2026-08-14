import { format } from 'date-fns';
import { toast } from 'sonner';
import { useSelectedQuery } from '@lib/state/query';
import { useLimitAlertState } from '@lib/state/limit';
import { useLimit, useQueryByID, useUpdateQueryStatus } from '@lib/api';
import { cn } from '@lib/utils';
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter, DialogHeader } from '@components/ui/dialog';
import { Button } from '@components/ui/button';
import { Progress } from '@components/ui/progress';
import { Spinner } from '@components/ui/spinner';
import { Badge } from '@components/ui/badge';
import { Separator } from '@components/ui/separator';
import { ExportButton } from '@components/export';
import { QUERY_COMPLETE, FETCH_INCOMPLETE, FETCH_CONTINUE, CLEAN_CONTINUE, PARSE_INCOMPLETE } from '@constants/status';
import { EQ, AND, OR, NOT } from '@constants/modifiers';
import type { ReactElement, FC } from 'react';
import type { SelectedQueryState, CurrentViewType } from '@state/query';
import type { LimitAlertState } from '@state/limit';
import type { Query, QueryTerm } from '@appTypes/query';

/** Reads the selected query out of the cache; the store only holds which id is selected. */
function useSelectedQueryData(): Query | null {
  const id = useSelectedQuery((state: SelectedQueryState): string | null => state.selectedQueryID);

  return useQueryByID(id);
}

export function QueryDetailsHeader(): ReactElement<FC> {
  const selectedQuery: Query | null = useSelectedQueryData();
  const currentView = useSelectedQuery((state: SelectedQueryState): CurrentViewType => state.currentView);
  const badgeClasses: string = cn({
    'bg-green-600/10 text-green-600 dark:bg-green-400/20': selectedQuery?.status === QUERY_COMPLETE,
    'bg-red-600/10 text-red-600 dark:bg-red-400/20': (
      selectedQuery?.status === FETCH_INCOMPLETE ||
      selectedQuery?.status === PARSE_INCOMPLETE
    ),
    'bg-zinc-600/10 text-zinc-600 dark:bg-zinc-400/20 dark:text-zinc-400': (
      selectedQuery?.status !== QUERY_COMPLETE && selectedQuery?.status !== FETCH_INCOMPLETE &&
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
  const selectedQuery: Query | null = useQueryByID(state.selectedQueryID);
  const limit = useLimit();
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const updateStatus = useUpdateQueryStatus();
  const handleClose = (): void => {
    if (state.currentView === 'complete') {
      state.clear();
      return;
    }

    state.removeQuery();
  };
  // Resumes the pipeline and switches to the progress view; the status arrives over the
  // WebSocket from there, and the footer swaps to the export button on completion.
  const resume = async (status: string): Promise<void> => {
    if (state.selectedQueryID == null) return;

    try {
      const response = await updateStatus.mutateAsync({ id: state.selectedQueryID, status });

      if (response.code !== 200) {
        console.error('an error occurred when updating query status', response);
        return;
      }

    } catch (error) {
      console.error('an error occurred when updating query status', error);
      toast.error('Could not resume the extraction', {
        description: 'Something went wrong asking the extractor to continue.'
      });
      return;
    }

    state.setCurrentView('progress');
  };
  const handleClick = async (): Promise<void> => {
    if (limit.count === 0) {
      limitAlertState.setType('maxed_out');
      limitAlertState.toggleShow();
      return;
    }

    await resume(FETCH_CONTINUE);
  };
  const isIncomplete: boolean = (
    selectedQuery?.status === (FETCH_INCOMPLETE as string) ||
    selectedQuery?.status === (PARSE_INCOMPLETE as string)
  );
  const isDisabled: boolean = !isIncomplete || limit.count === 0;

  return (
    <DialogFooter className="sm:justify-between">
      <Button
        variant="outline"
        className="cursor-pointer"
        disabled={state.currentView === 'progress'}
        onClick={handleClose}>
        Close
      </Button>
      <div className="grid grid-flow-col auto-cols-max gap-x-2">
        {/* Offered only for a paused extraction: a complete one exports through the button
            below, and one still running has nothing settled to export yet. Parsing what was
            already fetched costs no requests, so unlike the button beside it this stays
            available with an exhausted daily allowance. */}
        {isIncomplete && state.currentView !== 'progress' && (
          <Button
            variant="outline"
            className="cursor-pointer"
            disabled={updateStatus.isPending}
            onClick={(): void => { void resume(CLEAN_CONTINUE); }}>
            Export Data so Far
          </Button>
        )}
        {selectedQuery?.status !== QUERY_COMPLETE && (
          <Button variant="default"
            className="cursor-pointer"
            disabled={isDisabled || updateStatus.isPending}
            onClick={handleClick}>
            Complete Extraction
          </Button>
        )}
        {selectedQuery?.status === QUERY_COMPLETE && <ExportButton id={selectedQuery.id} />}
      </div>
    </DialogFooter>
  );
}

export function QueryDetails(): ReactElement<FC> {
  const selectedQuery: Query | null = useSelectedQueryData();
  const completedPercentage = selectedQuery != null ? Math.round(selectedQuery?.percentage * 100) : 0;

  return (
    <div className="grid grid-flow-row gap-y-2 overflow-y-auto max-h-[25rem]">
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
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">Requests Used</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery?.queriesUsed}
            </span>
          </div>
        </div>
        <div className="grid grid-flow-col grid-cols-8">
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">Rows Fetched</h3>
            <span className="text-sm text-muted-foreground">
              {selectedQuery?.rowsFetched}
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
        <div className="grid grid-flow-row gap-y-2">
          <h3 className="font-medium text-sm">Search Terms</h3>
          <ul className="grid grid-flow-row gap-y-2">
            {
              selectedQuery?.terms.map((item: QueryTerm, index: number): ReactElement<FC> => {
                let modifierLabel: string = '-';

                if (item.modifier === EQ) modifierLabel = 'Contains';
                if (item.modifier === NOT) modifierLabel = 'Does Not Contain';
                if (item.modifier === AND) modifierLabel = 'Also Contains';
                if (item.modifier === OR) modifierLabel = 'Or Contains';

                return (
                  <li key={`search-term-item-${index + 1}`}
                    className="grid grid-flow-col auto-cols-auto items-center justify-start gap-x-2">
                    <span className="text-sm text-muted-foreground font-medium">
                      {modifierLabel}
                    </span>
                    <span className="text-sm text-foreground truncate">
                      {item.term}
                    </span>
                  </li>
                );
              })
            }
          </ul>
        </div>
      </div>
    </div>
  );
}

export function QueryDetailsProgress(): ReactElement<FC> {
  const selectedQuery: Query | null = useSelectedQueryData();
  const progressPercentage: number = selectedQuery != null ? Math.round(selectedQuery.percentage * 100) : 0;

  return (
    <div className="grid grid-flow-row gap-y-2">
      <div className="grid grid-flow-col justify-start items-center">
        <Spinner />
        <span>We are preparing your file...</span>
      </div>
      <div className="grid grid-flow-col grid-cols-12 justify-between items-center">
        <Progress className="h-3 col-span-10" value={progressPercentage} />
        <span className="col-span-2 text-center">{progressPercentage}%</span>
      </div>
    </div>
  );
}

export function QueryDetailsCompletion(): ReactElement<FC> {
  const selectedQuery: Query | null = useSelectedQueryData();
  const progressPercentage: number = selectedQuery != null ? Math.round(selectedQuery.percentage * 100) : 0;

  return (
    <div className="grid grid-flow-row gap-y-4">
      <div className="grid grid-flow-row">
        <div className="grid grid-flow-col grid-cols-12">
          <div className="grid grid-flow-row col-span-6">
            <h3 className="font-medium text-sm">Extraction Completion</h3>
            <span className="text-sm text-muted-foreground">{progressPercentage}%</span>
          </div>
          <div className="grid grid-flow-row col-span-6">
            <h3 className="font-medium text-sm">Requests Used</h3>
            <span className="text-sm text-muted-foreground">{selectedQuery?.queriesUsed}</span>
          </div>
        </div>
      </div>
      <div className="grid grid-flow-row">
        <div className="grid grid-flow-col grid-cols-12">
          <div className="grid grid-flow-row col-span-6">
            <h3 className="font-medium text-sm">Rows Fetched</h3>
            <span className="text-sm text-muted-foreground">{selectedQuery?.rowsFetched}</span>
          </div>
        </div>
      </div>
      <Separator />
      <div className="grid grid-flow-col grid-cols-12">
        <div className="grid grid-flow-row col-span-6">
          <h3 className="font-medium text-sm">Time Zone</h3>
          <span className="text-sm text-muted-foreground">
            {selectedQuery?.timezone}
          </span>
        </div>
      </div>
      <div className="grid grid-flow-col grid-cols-12">
        <div className="grid grid-flow-row col-span-6">
          <h3 className="font-medium text-sm">From</h3>
          <span className="text-sm text-muted-foreground">
            {selectedQuery?.startDate != null ? format(new Date(selectedQuery?.startDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
          </span>
        </div>
        <div className="grid grid-flow-row col-span-6">
          <h3 className="font-medium text-sm">To</h3>
          <span className="text-sm text-muted-foreground">
            {selectedQuery?.endDate != null ? format(new Date(selectedQuery?.endDate), 'yyyy/MM/dd hh:mm:ss a') : '-'}
          </span>
        </div>
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
    // Base UI has no onInteractOutside; dismissal reasons arrive through onOpenChange. Filtering
    // on 'outside-press' preserves the previous behaviour exactly: this dialog closes by clicking
    // outside it and by nothing else (Escape did not close it before either, because the `open`
    // prop is controlled and Radix's escape handler had no onOpenChange to call).
    <Dialog
      open={state.selectedQueryID != null}
      onOpenChange={(open, eventDetails): void => {
        if (!open && eventDetails.reason === 'outside-press') handleDialogClose();
      }}
    >
      <DialogContent showCloseButton={false}>
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
