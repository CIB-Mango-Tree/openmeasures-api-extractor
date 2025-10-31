import { useFetchingQueryState } from '@lib/state/query';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@components/ui/card';
import { Progress } from '@components/ui/progress';
import { Spinner } from '@components/ui/spinner';
import { ExportButton } from '@components/export';
import { QUERY_COMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { FetchingQueryState } from '@state/query';

export function QueryResultView(): ReactElement<FC> {
  const fetchQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const progressPercentage: number = fetchQueryState.query != null ? Math.round(fetchQueryState.query.percentage * 100) : 0;

  return (
    <Card className="col-span-4 h-min">
      <CardHeader>
        <CardTitle>Export data</CardTitle>
        <CardDescription>Apply filters first to start an extraction</CardDescription>
      </CardHeader>
      {fetchQueryState.showProgress ?? (
        <CardContent>
          <Spinner />
          <span>We are preparing your file...</span>
          <div className="grid grid-flow-col justify-between">
            <Progress value={progressPercentage} />
            <span>{progressPercentage}%</span>
          </div>
        </CardContent>
      )}
      <CardFooter>
        <ExportButton
          id={fetchQueryState.query?.id}
          disabled={fetchQueryState.query == null || fetchQueryState.query.status !== QUERY_COMPLETE} />
      </CardFooter>
    </Card>
  );
}
