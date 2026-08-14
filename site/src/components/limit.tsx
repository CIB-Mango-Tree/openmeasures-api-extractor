import { toast } from 'sonner';
import { useLimitAlertState } from '@state/limit';
import { useFetchingQueryState } from '@state/query';
import { useLimit, useQueryByID, useUpdateQueryStatus } from '@lib/api';
import { cn } from '@lib/utils';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@components/ui/alert-dialog';
import { AlertCircleIcon, TriangleAlert } from 'lucide-react';
import { Button } from '@components/ui/button';
import { FETCH_CONTINUE, CLEAN_CONTINUE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { Query } from '@appTypes/query';
import type { LimitAlertState } from '@state/limit';
import type { FetchingQueryState } from '@state/query';

const DAILY_LIMIT = 39;

export function LimitAlert(): ReactElement<FC> {
  const { count } = useLimit();
  const alertClasses: string = cn('col-span-8', {
    'border-destructive': count === 0
  });

  return (
    <Alert variant={count === 0 ? 'destructive' : 'default'} className={alertClasses}>
      <AlertCircleIcon />
      <AlertTitle>Daily query limit</AlertTitle>
      <AlertDescription>
        You are able to pull up to 39 search queries in a day with the API extractor due to protocols of Open Measures.
        Each query can contain a max of 10,000 rows of data. You may use one or multiple queries to complete an extraction.
        Queries replenish each day at at 00:00:00 UTC.
      </AlertDescription>
    </Alert>
  );
}

export function LimitCounter(): ReactElement<FC> {
  const { count } = useLimit();

  return (
    <Card className="col-span-4 justify-start gap-0 py-4">
      <CardHeader>
        <CardTitle className="font-normal">Queries left today</CardTitle>
      </CardHeader>
      <CardContent>
        <span className="text-xl font-bold">
          {count}
          <span className="text-muted-foreground">/{DAILY_LIMIT}</span>
        </span>
      </CardContent>
      <CardFooter>
        <p className="text-sm text-muted-foreground">{DAILY_LIMIT - count} used</p>
      </CardFooter>
    </Card>
  );
}

export function LimitAlertContinueDialog(): ReactElement<FC> {
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const query: Query | null = useQueryByID(fetchingQueryState.queryID);
  const updateStatus = useUpdateQueryStatus();
  const handleDiscard = (): void => {
    limitAlertState.toggleShow();
    fetchingQueryState.removeQuery();
    if (fetchingQueryState.showProgress) fetchingQueryState.toggleShow();
  };
  // Both actions resume the pipeline and return; the progress card follows the status from there,
  // and the export button enables on its own once the query reports complete.
  const resume = async (status: string, failureMessage: string): Promise<void> => {
    if (fetchingQueryState.queryID == null) return;

    try {
      await updateStatus.mutateAsync({ id: fetchingQueryState.queryID, status });

    } catch (error) {
      console.error(failureMessage, error);
      toast.error('Could not resume the extraction', {
        description: 'Something went wrong asking the extractor to continue.'
      });
      return;
    }

    limitAlertState.toggleShow();
  };
  const handleContinue = (): Promise<void> => resume(
    FETCH_CONTINUE, 'an error occurred when resuming the extraction'
  );
  // Parses what has already been fetched instead of spending more of the daily allowance on it,
  // so this is never gated on the remaining request count.
  const handleExtractSoFar = (): Promise<void> => resume(
    CLEAN_CONTINUE, 'an error occurred when preparing the partial extraction'
  );

  return (
    // Wider than the default: three actions side by side overflow the sm max-width this dialog
    // ships with. The data-size prefix has to be repeated for tailwind-merge to treat it as the
    // same class and let this one win.
    <AlertDialogContent className="data-[size=default]:sm:max-w-xl">
      <AlertDialogHeader>
        <AlertDialogTitle>Your request has exceeded query limit</AlertDialogTitle>
        <AlertDialogDescription>
          The API extractor has reached its single request limit of 10,000 rows, extracting only{' '}
          {query != null ? Math.round(query.percentage * 100) : 0}% of your filtered query.
          If you want to proceed, you can either export this partial data, or use more remaining queries to complete your query.
        </AlertDialogDescription>
      </AlertDialogHeader>
      {/* Wraps rather than overflowing if the window is narrower than the three buttons need. */}
      <AlertDialogFooter className="sm:flex-wrap">
        <AlertDialogCancel onClick={handleDiscard}
          className="cursor-pointer">
          Discard
        </AlertDialogCancel>
        <Button
          variant="outline"
          onClick={(): void => { void handleExtractSoFar(); }}
          disabled={updateStatus.isPending}
          className="cursor-pointer">
          Extract Data so Far
        </Button>
        <AlertDialogAction onClick={(): void => { void handleContinue(); }}
          disabled={updateStatus.isPending}
          className="cursor-pointer">
          Complete with more requests
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}

export function LimitAlertMaxedOutDialog(): ReactElement<FC> {
  const toggleShow = useLimitAlertState((state: LimitAlertState): () => void => state.toggleShow);

  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle className="inline-flex gap-x-2">
          <TriangleAlert />
          You do not have enough requests left today
        </AlertDialogTitle>
        <AlertDialogDescription>
          The number of queries needed to complete the remainder of your request exceeds the number of available queries you have today.
          If you want to proceed, you can export max partial data with all available queries.
          You will have the option to complete the remainder of any partial data extractions after your request limit is replenished.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={(): void => toggleShow()}
          className="cursor-pointer">
          Close
        </AlertDialogCancel>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}

export function LimitAlertDialog(): ReactElement<FC> {
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);

  return (
    <AlertDialog open={limitAlertState.show}>
      {limitAlertState.type === 'continue' && <LimitAlertContinueDialog />}
      {limitAlertState.type === 'maxed_out' && <LimitAlertMaxedOutDialog />}
    </AlertDialog>
  );
}
