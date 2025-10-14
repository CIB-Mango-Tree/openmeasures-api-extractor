import { Card } from '@components/ui/card';
import { Alert } from '@components/ui/alert';
import { useLimitState } from '@state/limit';
import type { ReactElement, FC } from 'react';
import type { LimitState } from '@state/limit';

export function LimitAlert(): ReactElement<FC> {
  return (
    <Alert></Alert>
  );
}

export function LimitCounter(): ReactElement<FC> {
  return (
    <Card></Card>
  );
}
