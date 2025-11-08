import { useState, useMemo, useEffect } from 'react';
import { useLimitState, useLimitAlertState } from '@state/limit';
import { useFetchingQueryState } from '@state/query';
import { formatISO } from 'date-fns';
import { POSTQuery } from '@lib/fetch/query';
import { SquarePlus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent } from '@components/ui/card';
import { Field, FieldLabel, FieldSet, FieldGroup } from '@components/ui/field';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@components/ui/select';
import { Button } from '@components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@components/ui/tooltip';
import DateTimePicker from '@components/date-time-picker';
import SearchTermInput from '@components/search-term-input';
import { QUERY_COMPLETE } from '@constants/status';
import { EQ } from '@constants/modifiers';
import type { ReactElement, FC, FormEvent } from 'react';
import type { SearchTermValues, SearchTermChangeValues } from '@appTypes/term';
import type { CreateQueryPayload, QueryTerm, Query } from '@appTypes/query';
import type { LimitState, LimitAlertState } from '@state/limit';
import type { FetchingQueryState } from '@state/query';

export type SearchTermStateValues = SearchTermValues & { first?: boolean; };
export type SearchTermMap = { [index: string]: SearchTermValues; };

export function QueryBuilder(): ReactElement<FC> {
  const defaultTimezone = useMemo<string>((): string => (
    new Intl
      .DateTimeFormat('en-US', { timeZoneName: 'long' })
      .formatToParts(new Date())
      .find((item: Intl.DateTimeFormatPart): boolean => item.type === 'timeZoneName')?.value as string
  ), []);
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const limitState = useLimitState((state: LimitState): LimitState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const [submitDisabled, setSubmitDisabled] = useState<boolean>(false);
  const [timezone, setTimezone] = useState<string>(defaultTimezone);
  const [platform, setPlatform] = useState<string>('');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [searchTerms, setSearchTerms] = useState<SearchTermMap>({
    'default': { modifier: EQ, term: '' }
  });
  const isStateEmpty: boolean = (
    (timezone.length === 0 || timezone === defaultTimezone) && platform.length === 0 && startDate == null && endDate == null &&
    Object.keys(searchTerms).length === 1 && searchTerms['default'].term.length === 0
  );
  const isNotSubmittable: boolean = (
    timezone.length === 0 || platform.length === 0 || startDate == null || endDate == null || searchTerms['default'].term.length === 0
  );
  const handleStartDateChange = (date?: Date): void => setStartDate(date || null);
  const handleEndDateChange = (date?: Date): void => setEndDate(date || null);
  const handleSearchTermChange = (changeValues: SearchTermChangeValues): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => ({
      ...state,
      [changeValues.index]: { modifier: changeValues.modifier, term: changeValues.term }
    }));
  };
  const handleSearchTermDelete = (key: string): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => {
      const { [key]: _, ...terms } = state;

      return terms;
    });
  };
  const handleSearchTermAdd = (): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => ({
      ...state,
      [self.crypto.randomUUID()]: { modifier: '', term: '' }
    }));
  };
  const handleClear = (): void => {
    if (timezone.length > 0 && timezone !== defaultTimezone) setTimezone(defaultTimezone);
    if (startDate != null) setStartDate(null);
    if (endDate != null) setEndDate(null);
    if (platform.length > 0) setPlatform('');
    if (Object.keys(searchTerms).length > 1 || searchTerms['default'].term.length > 0) setSearchTerms({
      ['default']: { modifier: EQ, term: '' }
    });
  };
  const handleSubmit = async (event: FormEvent): Promise<void> => {
    event.preventDefault();

    if (limitState.count === 0) {
      limitAlertState.setType('maxed_out');
      limitAlertState.toggleShow();
      return;
    }

    setSubmitDisabled(true);

    const payload: CreateQueryPayload = {
      timezone,
      platform,
      start_date: formatISO(startDate as Date, { format: 'extended' }),
      end_date: formatISO(endDate as Date, { format: 'extended' }),
      terms: Object.values(searchTerms) as Array<QueryTerm>
    };
    const response = await POSTQuery(payload);

    handleClear();
    fetchingQueryState.setQuery({
      id: response.data.id,
      createdAt: response.data.created_at,
      updatedAt: response.data.updated_at,
      platform: response.data.platform,
      status: response.data.status,
      timezone: response.data.timezone,
      startDate: response.data.start_date,
      endDate: response.data.end_date,
      rowsFetched: response.data.rows_fetched,
      queriesUsed: response.data.queries_used,
      percentage: response.data.percentage,
      terms: response.data.terms
    });
    fetchingQueryState.toggleShow();
  };

  useEffect((): void => {
    if (fetchingQueryState.query == null || fetchingQueryState.query.status !== QUERY_COMPLETE) return;

    fetchingQueryState.toggleShow();
    setSubmitDisabled(false);
  }, [fetchingQueryState.query]);

  return (
    <Card className="col-span-8" suppressHydrationWarning>
      <CardHeader>
        <CardTitle>Start Here</CardTitle>
        <CardDescription>Narrow down your search with filters below</CardDescription>
        <CardAction className="self-center">
          <Button
            onClick={handleClear}
            disabled={submitDisabled || isStateEmpty}
            className="cursor-pointer">
            Clear All
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
            <FieldSet>
              <FieldGroup>
                <Field className="w-1/2">
                  <FieldLabel>Time Zone</FieldLabel>
                  <Select disabled={submitDisabled} value={timezone} onValueChange={setTimezone}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a timezone" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectLabel>North America</SelectLabel>
                        <SelectItem value="Eastern Standard Time">Eastern Standard Time (EST)</SelectItem>
                        <SelectItem value="Central Standard Time">Central Standard Time (CST)</SelectItem>
                        <SelectItem value="Mountain Standard Time">Mountain Standard Time (MST)</SelectItem>
                        <SelectItem value="Pacific Standard Time">Pacific Standard Time (PST)</SelectItem>
                        <SelectItem value="Alaska Standard Time">Alaska Standard Time (AKST)</SelectItem>
                        <SelectItem value="Hawaii Standard Time">Hawaii Standard Time (HST)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Europe & Africa</SelectLabel>
                        <SelectItem value="Greenwich Mean Time">Greenwich Mean Time (GMT)</SelectItem>
                        <SelectItem value="Central European Time">Central European Time (CET)</SelectItem>
                        <SelectItem value="Eastern European Time">Eastern European Time (EET)</SelectItem>
                        <SelectItem value="Western European Summer Time">
                          Western European Summer Time (WEST)
                        </SelectItem>
                        <SelectItem value="Central Africa Time">Central Africa Time (CAT)</SelectItem>
                        <SelectItem value="East Africa Time">East Africa Time (EAT)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Asia</SelectLabel>
                        <SelectItem value="Moscow Time">Moscow Time (MSK)</SelectItem>
                        <SelectItem value="India Standard Time">India Standard Time (IST)</SelectItem>
                        <SelectItem value="China Standard Time">China Standard Time (CST)</SelectItem>
                        <SelectItem value="Japan Standard Time">Japan Standard Time (JST)</SelectItem>
                        <SelectItem value="Korea Standard Time">Korea Standard Time (KST)</SelectItem>
                        <SelectItem value="Indonesia Central Standard Time">
                          Indonesia Central Standard Time (WITA)
                        </SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Australia & Pacific</SelectLabel>
                        <SelectItem value="Australian Western Standard Time">
                          Australian Western Standard Time (AWST)
                        </SelectItem>
                        <SelectItem value="Australian Central Standard Time">
                          Australian Central Standard Time (ACST)
                        </SelectItem>
                        <SelectItem value="Australian Eastern Standard Time">
                          Australian Eastern Standard Time (AEST)
                        </SelectItem>
                        <SelectItem value="New Zealand Standard Time">New Zealand Standard Time (NZST)</SelectItem>
                        <SelectItem value="Fiji Time">Fiji Time (FJT)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>South America</SelectLabel>
                        <SelectItem value="Argentina Time">Argentina Time (ART)</SelectItem>
                        <SelectItem value="Bolivia Time">Bolivia Time (BOT)</SelectItem>
                        <SelectItem value="Brasilia Time">Brasilia Time (BRT)</SelectItem>
                        <SelectItem value="Chile Standard Time">Chile Standard Time (CLT)</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </Field>
              </FieldGroup>
              <FieldGroup>
                <div className="grid grid-flow-col grid-cols-8 gap-x-2">
                  <Field className="col-span-4">
                    <FieldLabel>From</FieldLabel>
                    <DateTimePicker value={startDate} disabled={submitDisabled} onChange={handleStartDateChange} />
                  </Field>
                  <Field className="col-span-4">
                    <FieldLabel>To</FieldLabel>
                    <DateTimePicker value={endDate} disabled={submitDisabled} onChange={handleEndDateChange} />
                  </Field>
                </div>
              </FieldGroup>
              <FieldGroup>
                <Field className="w-1/2">
                  <FieldLabel>Social Media Platform</FieldLabel>
                  <Select disabled={submitDisabled} value={platform} onValueChange={setPlatform}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="truth_social">Truth Social</SelectItem>
                      <SelectItem value="bluesky">Bleusky</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
              </FieldGroup>
              <FieldGroup>
                <FieldLabel>Search</FieldLabel>
                {Object.entries(searchTerms).map((item: [string, SearchTermValues]): ReactElement<FC> => {
                  const index: string = item[0];
                  const entry: SearchTermValues = item[1];

                  return <SearchTermInput
                    key={index}
                    index={index}
                    disabled={submitDisabled}
                    modifier={entry.modifier}
                    term={entry.term}
                    onChange={handleSearchTermChange}
                    onButtonCLick={handleSearchTermDelete} />
                })}
                <Field orientation="horizontal">
                  <Tooltip delayDuration={1000}>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="link"
                        className="cursor-pointer has-[>svg]:px-0 p-0"
                        disabled={submitDisabled}
                        onClick={handleSearchTermAdd}>
                        <SquarePlus className="size-6" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      Add search term
                    </TooltipContent>
                  </Tooltip>
                </Field>
              </FieldGroup>
            </FieldSet>
            <Field orientation="horizontal">
              <Button type="submit" className="cursor-pointer" disabled={submitDisabled || isNotSubmittable}>
                Apply
              </Button>
            </Field>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
