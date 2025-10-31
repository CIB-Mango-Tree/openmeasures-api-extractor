import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@components/ui/alert';
import { AlertCircleIcon } from 'lucide-react';
import { useLimitState } from '@state/limit';
import type { ReactElement, FC } from 'react';
import type { LimitState } from '@state/limit';

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
