import { useFetchingQueryState } from '@lib/state/query';
import { Sheet, FileJson2, FileSpreadsheet } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@components/ui/card';
import { Button } from '@components/ui/button';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@components/ui/dropdown-menu';
import { Progress } from '@components/ui/progress';
import { QUERY_COMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { FetchingQueryState } from '@state/query';

export function QueryResultView(): ReactElement<FC> {
  const fetchQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const baseUrl: string = `${import.meta.env.VITE_API_URL}/api/queries/${fetchQueryState.query?.id}/download`;
  const querySelected: boolean = fetchQueryState.query != null && fetchQueryState.query.status == QUERY_COMPLETE;
  const progressPercentage: number = fetchQueryState.query != null ? Math.round(fetchQueryState.query.percentage * 100) : 0;

  return (
    <Card className="col-span-4 h-min">
      <CardHeader>
        <CardTitle>Export data</CardTitle>
        <CardDescription>Apply filters first to start an extraction</CardDescription>
      </CardHeader>
      {fetchQueryState.showProgress ?? (
        <CardContent>
          <span>We are preparing your file...</span>
          <div className="grid grid-flow-col justify-between">
            <Progress value={progressPercentage} />
            {fetchQueryState.query != null && (
              <span>{progressPercentage}%</span>
            )}
          </div>
        </CardContent>
      )}
      <CardFooter>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              disabled={fetchQueryState.query == null || fetchQueryState.query.status !== QUERY_COMPLETE}
              className="cursor-pointer">
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <a className="inline-flex items-center" href={querySelected ? `${baseUrl}/csv` : ''}>
                <FileSpreadsheet />
                <span className="pl-1 font-bold">CSV</span>
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <a className="inline-flex items-center" href={querySelected ? `${baseUrl}/excel` : ''}>
                <Sheet />
                <span className="pl-1 font-bold">EXCEL</span>
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <a className="inline-flex items-center" href={querySelected ? `${baseUrl}/json` : ''}>
                <FileJson2 />
                <span className="pl-1 font-bold">JSON</span>
              </a>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardFooter>
    </Card>
  );
}
