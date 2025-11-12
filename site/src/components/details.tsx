import { format } from 'date-fns';
import { useSelectedQuery } from '@lib/state/query';
import { useLimitState, useLimitAlertState } from '@lib/state/limit';
import { PATCHQuery } from '@lib/fetch/query';
import { mapResponseToQuery } from '@lib/map';
import { cn } from '@lib/utils';
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter, DialogHeader } from '@components/ui/dialog';
import { Button } from '@components/ui/button';
import { Progress } from '@components/ui/progress';
import { Spinner } from '@components/ui/spinner';
import { Badge } from '@components/ui/badge';
import { Separator } from '@components/ui/separator';
import { ExportButton } from '@components/export';
import { QUERY_COMPLETE, FETCH_INCOMPLETE, FETCH_CONTINUE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE } from '@constants/status';
import { EQ, AND, OR, NOT } from '@constants/modifiers';
import type { ReactElement, FC } from 'react';
import type { SelectedQueryState, CurrentViewType } from '@state/query';
import type { LimitState, LimitAlertState } from '@state/limit';
import type { Query, QueryResponse, QueryTerm } from '@appTypes/query';
import type { APIResponse } from '@appTypes/fetch';

export function QueryDetailsHeader(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
  const currentView = useSelectedQuery((state: SelectedQueryState): CurrentViewType => state.currentView);
  const badgeClasses: string = cn({
    'bg-green-600/10 text-green-600 dark:bg-green-400/20': selectedQuery?.status === QUERY_COMPLETE,
    'bg-red-600/10 text-red-600 dark:bg-red-400/20': (
      selectedQuery?.status === FETCH_INCOMPLETE || selectedQuery?.status === CLEAN_INCOMPLETE ||
      selectedQuery?.status === PARSE_INCOMPLETE
    ),
    'bg-zinc-600/10 text-zinc-600 dark:bg-zinc-400/20 dark:text-zinc-400': (
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
  const limitState = useLimitState((state: LimitState): LimitState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const handleClose = (): void => {
    if (state.currentView === 'complete') {
      state.clear();
      return;
    }

    state.removeQuery();
  };
  const handleClick = async (): Promise<void> => {
    if (limitState.count === 0) {
      limitAlertState.setType('maxed_out');
      limitAlertState.toggleShow();
      return;
    }

    const response: APIResponse<QueryResponse> = await PATCHQuery(state.selectedQuery?.id as string, FETCH_CONTINUE);
    const query: Query = mapResponseToQuery(response.data);

    state.setQuery(query);
    state.setCurrentView('progress');
  };
  const isDisabled: boolean = (
    state.selectedQuery?.status !== (FETCH_INCOMPLETE as string) &&
    state.selectedQuery?.status !== (CLEAN_INCOMPLETE as string) &&
    state.selectedQuery?.status !== (PARSE_INCOMPLETE as string)
  );

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
        <Button variant="default"
          className="cursor-pointer"
          disabled={isDisabled}
          onClick={handleClick}>
          Complete Extraction
        </Button>
      )}
      {state.selectedQuery?.status === QUERY_COMPLETE && <ExportButton id={state.selectedQuery.id} />}
    </DialogFooter>
  );
}

export function QueryDetails(): ReactElement<FC> {
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
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
            <span className="text-sm text-muted-foreground">{selectedQuery?.queriesUsed}</span>
          </div>
        </div>
        <div className="grid grid-flow-col grid-cols-8">
          <div className="grid grid-flow-row col-span-4">
            <h3 className="font-medium text-sm">Rows Fetched</h3>
            <span className="text-sm text-muted-foreground">{selectedQuery?.rowsFetched}</span>
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
          <ul className="grid grid-flow-row pl-2">
            {
              selectedQuery?.terms.map((item: QueryTerm, index: number): ReactElement<FC> => {
                let modifierLabel: string = '-';

                if (item.modifier === EQ) modifierLabel = 'Contains';
                if (item.modifier === NOT) modifierLabel = 'Does Not Contain';
                if (item.modifier === AND) modifierLabel = 'Also Contains';
                if (item.modifier === OR) modifierLabel = 'Or Contains';

                return (
                  <li key={`search-term-item-${index + 1}`}
                    className="grid grid-flow-col grid-cols-12 items-center justify-start">
                    <span className="text-sm text-muted-foreground font-medium col-span-3">
                      {modifierLabel}
                    </span>
                    <span className="text-sm text-foreground truncate col-span-9">
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
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
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
  const selectedQuery = useSelectedQuery((state: SelectedQueryState): Query | null => state.selectedQuery);
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
