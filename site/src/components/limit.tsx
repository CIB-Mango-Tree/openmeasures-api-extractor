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
    <Card className="h-min col-span-4 justify-start">
      <CardHeader>
        <CardTitle className="font-normal text-3xl">Queries left today</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-4xl text-muted-foreground"><span className="text-zinc-900">{count}</span>/39</p>
      </CardContent>
      <CardFooter>
        <p className="text-muted-foreground">{39 - count} used</p>
      </CardFooter>
    </Card>
  );
}
