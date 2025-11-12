import { useLimitState, useLimitAlertState } from '@state/limit';
import { useFetchingQueryState, useQueries } from '@state/query';
import { PATCHQuery } from '@lib/fetch/query';
import { mapResponseToQuery } from '@lib/map';
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
import { FETCH_CONTINUE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { Query, QueryResponse } from '@appTypes/query';
import type { APIResponse } from '@appTypes/fetch';
import type { LimitState, LimitAlertState } from '@state/limit';
import type { FetchingQueryState, QueriesState } from '@state/query';

export function LimitAlert(): ReactElement<FC> {
  const count = useLimitState((state: LimitState): number => state.count);

  return (
    <Alert variant={count === 0 ? 'destructive' : 'default'} className="col-span-8">
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
  const count = useLimitState((state: LimitState): number => state.count);

  return (
    <Card className="col-span-4 justify-start gap-0 py-4">
      <CardHeader>
        <CardTitle className="font-normal">Queries left today</CardTitle>
      </CardHeader>
      <CardContent>
        <span className="text-xl font-bold">
          {count}
          <span className="text-muted-foreground">/39</span>
        </span>
      </CardContent>
      <CardFooter>
        <p className="text-sm text-muted-foreground">{39 - count} used</p>
      </CardFooter>
    </Card>
  );
}

export function LimitAlertContinueDialog(): ReactElement<FC> {
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const queriesState = useQueries((state: QueriesState): QueriesState => state);
  const handleDiscard = (): void => {
    limitAlertState.toggleShow();
    fetchingQueryState.removeQuery();
    fetchingQueryState.toggleShow();
  };
  const handleContinue = async (): Promise<void> => {
    const response: APIResponse<QueryResponse> = await PATCHQuery(fetchingQueryState.query?.id as string, FETCH_CONTINUE);
    const query: Query = mapResponseToQuery(response.data);

    fetchingQueryState.setQuery(query);
    queriesState.update(query);
    limitAlertState.toggleShow();
  };

  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Your request has exceeded query limit</AlertDialogTitle>
        <AlertDialogDescription>
          The API extractor has reached its single request limit of 10,000 rows, extracting only{' '}
          {fetchingQueryState.query ? Math.round(fetchingQueryState.query.percentage * 100) : 0}% of your filtered query.
          If you want to proceed, you can either export this partial data, or use more remaining queries to complete your query.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel onClick={handleDiscard}
          className="cursor-pointer">
          Discard
        </AlertDialogCancel>
        <AlertDialogAction onClick={handleContinue}
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
        <AlertDialogTitle>
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
