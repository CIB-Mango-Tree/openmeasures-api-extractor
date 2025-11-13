import { useState, useMemo, useEffect } from 'react';
import { useLimitState, useLimitAlertState } from '@state/limit';
import { useFetchingQueryState, useQueries } from '@state/query';
import { formatISO } from 'date-fns';
import { POSTQuery } from '@lib/fetch/query';
import { GETPlatforms } from '@lib/fetch/platform';
import { mapResponseToQuery } from '@lib/map';
import { SquarePlus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent } from '@components/ui/card';
import { Field, FieldLabel, FieldSet, FieldGroup, FieldError } from '@components/ui/field';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@components/ui/select';
import { Button } from '@components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@components/ui/tooltip';
import DateTimePicker from '@components/date-time-picker';
import SearchTermInput from '@components/search-term-input';
import { QUERY_COMPLETE } from '@constants/status';
import { EQ } from '@constants/modifiers';
import type { ReactElement, FC, FormEvent } from 'react';
import type { SearchTermValues, SearchTermChangeValues } from '@appTypes/term';
import type { CreateQueryPayload, QueryTerm, Query, QueryResponse } from '@appTypes/query';
import type { Platform } from '@appTypes/platform';
import type { APICollectionResponse, APIResponse, APIErrorCollectionResponse, ValidationError } from '@appTypes/fetch';
import type { LimitState, LimitAlertState } from '@state/limit';
import type { FetchingQueryState, QueriesState } from '@state/query';

export type SearchTermMap = { [index: string]: SearchTermValues; };

export function QueryBuilder(): ReactElement<FC> {
  const defaultTimezone = useMemo<string>((): string => new Intl.DateTimeFormat().resolvedOptions().timeZone, []);
  const queriesState = useQueries((state: QueriesState): QueriesState => state);
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const limitState = useLimitState((state: LimitState): LimitState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const [platforms, setPlatforms] = useState<Array<Platform>>([]);
  const [startDateError, setStartDateError] = useState<ValidationError | null>(null);
  const [endDateError, setEndDateError] = useState<ValidationError | null>(null);
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
    timezone.length === 0 || platform.length === 0 || startDate == null || endDate == null ||
    !Object.values(searchTerms).every((item: SearchTermValues): boolean => item.modifier.length > 0 && item.term.length > 0)
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
    if (startDateError != null) setStartDateError(null);
    if (endDateError != null) setEndDateError(null);
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

    if (response.code === 422) {
      const validationErrors: Array<ValidationError> = (response as APIErrorCollectionResponse<ValidationError>).error;

      for (const err of validationErrors) {
        if (err.loc.includes('start_date') && err.type === 'date_past') {
          setStartDateError(err);
          continue;
        }

        if (err.loc.includes('end_date') && err.type === 'date_past') {
          setEndDateError(err);
          continue;
        }

        console.error('an error occurred when attempting to create query', err);
      }

      setSubmitDisabled(false);
      return;
    }

    const query: Query = mapResponseToQuery((response as APIResponse<QueryResponse>).data);

    handleClear();
    fetchingQueryState.setQuery(query);
    fetchingQueryState.toggleShow();
    queriesState.push(query);
  };

  useEffect((): void => {
    const func = async (): Promise<void> => {
      const response: APICollectionResponse<Platform> = await GETPlatforms();
      setPlatforms(response.data);
    };

    func();
  }, []);
  useEffect((): void => {
    if (fetchingQueryState.query == null || fetchingQueryState.query.status !== QUERY_COMPLETE) return;
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
                        <SelectItem value="America/New_York">Eastern Standard Time (EST)</SelectItem>
                        <SelectItem value="America/Chicago">Central Standard Time (CST)</SelectItem>
                        <SelectItem value="America/Denver">Mountain Standard Time (MST)</SelectItem>
                        <SelectItem value="America/Los_Angeles">Pacific Standard Time (PST)</SelectItem>
                        <SelectItem value="America/Anchorage">Alaska Standard Time (AKST)</SelectItem>
                        <SelectItem value="Pacific/Honolulu">Hawaii Standard Time (HST)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Europe & Africa</SelectLabel>
                        <SelectItem value="Europe/London">Greenwich Mean Time (GMT)</SelectItem>
                        <SelectItem value="Europe/Paris">Central European Time (CET)</SelectItem>
                        <SelectItem value="Europe/Athens">Eastern European Time (EET)</SelectItem>
                        <SelectItem value="Europe/Lisbon">
                          Western European Summer Time (WEST)
                        </SelectItem>
                        <SelectItem value="Africa/Maputo">Central Africa Time (CAT)</SelectItem>
                        <SelectItem value="Africa/Nairobi">East Africa Time (EAT)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Asia</SelectLabel>
                        <SelectItem value="Europe/Moscow">Moscow Time (MSK)</SelectItem>
                        <SelectItem value="Asia/Kolkata">India Standard Time (IST)</SelectItem>
                        <SelectItem value="Asia/Shanghai">China Standard Time (CST)</SelectItem>
                        <SelectItem value="Asia/Tokyo">Japan Standard Time (JST)</SelectItem>
                        <SelectItem value="Asia/Seoul">Korea Standard Time (KST)</SelectItem>
                        <SelectItem value="Asia/Makassar">
                          Indonesia Central Standard Time (WITA)
                        </SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>Australia & Pacific</SelectLabel>
                        <SelectItem value="Australia/Perth">
                          Australian Western Standard Time (AWST)
                        </SelectItem>
                        <SelectItem value="Australia/Adelaide">
                          Australian Central Standard Time (ACST)
                        </SelectItem>
                        <SelectItem value="Australia/Sydney">
                          Australian Eastern Standard Time (AEST)
                        </SelectItem>
                        <SelectItem value="Pacific/Auckland">New Zealand Standard Time (NZST)</SelectItem>
                        <SelectItem value="Pacific/Fiji">Fiji Time (FJT)</SelectItem>
                      </SelectGroup>
                      <SelectGroup>
                        <SelectLabel>South America</SelectLabel>
                        <SelectItem value="America/Argentina/Buenos_Aires">Argentina Time (ART)</SelectItem>
                        <SelectItem value="America/La_Paz">Bolivia Time (BOT)</SelectItem>
                        <SelectItem value="America/Sao_Paulo">Brasilia Time (BRT)</SelectItem>
                        <SelectItem value="America/Santiago">Chile Standard Time (CLT)</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </Field>
              </FieldGroup>
              <FieldGroup>
                <div className="grid grid-flow-col grid-cols-8 gap-x-2">
                  <Field className="col-span-4">
                    <FieldLabel>From</FieldLabel>
                    <DateTimePicker
                      value={startDate}
                      disabled={submitDisabled}
                      invalid={startDateError != null}
                      onChange={handleStartDateChange} />
                    <FieldError errors={startDateError != null ? [{ message: startDateError?.msg }] : undefined} />
                  </Field>
                  <Field className="col-span-4">
                    <FieldLabel>To</FieldLabel>
                    <DateTimePicker
                      value={endDate}
                      disabled={submitDisabled}
                      invalid={endDateError != null}
                      onChange={handleEndDateChange} />
                    <FieldError errors={endDateError != null ? [{ message: endDateError?.msg }] : undefined} />
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
                      {platforms.map((item: Platform, index: number): ReactElement<FC> => (
                        <SelectItem key={`platform-item-${index + 1}`} value={item.value}>
                          {item.readable}
                        </SelectItem>
                      ))}
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
                    onButtonCLick={handleSearchTermDelete} />;
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
