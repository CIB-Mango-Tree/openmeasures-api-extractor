import { useFetchingQueryState } from '@lib/state/query';
import { useQueryByID } from '@lib/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@components/ui/card';
import { Progress } from '@components/ui/progress';
import { Spinner } from '@components/ui/spinner';
import { ExportButton } from '@components/export';
import { QUERY_COMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { Query } from '@appTypes/query';
import type { FetchingQueryState } from '@state/query';

export function QueryResultView(): ReactElement<FC> {
  const fetchQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const query: Query | null = useQueryByID(fetchQueryState.queryID);
  const progressPercentage: number = query != null ? Math.round(query.percentage * 100) : 0;

  return (
    <Card className="col-span-4 h-min">
      <CardHeader>
        <CardTitle>Export data</CardTitle>
        <CardDescription>Apply filters first to start an extraction</CardDescription>
      </CardHeader>
      {fetchQueryState.showProgress && (
        <CardContent>
          <div className="grid grid-flow-col justify-start items-center">
            <Spinner />
            <span className="pl-2">We are preparing your file...</span>
          </div>
          <div className="grid grid-flow-col grid-cols-12 justify-between items-center">
            <Progress className="h-3 col-span-10" value={progressPercentage} />
            <span className="col-span-2 text-center">{progressPercentage}%</span>
          </div>
        </CardContent>
      )}
      <CardFooter>
        <ExportButton
          id={query?.id}
          disabled={query == null || query.status !== QUERY_COMPLETE} />
      </CardFooter>
    </Card>
  );
}
