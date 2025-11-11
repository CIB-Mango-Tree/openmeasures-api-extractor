import { useState, useRef, useMemo, useEffect } from 'react';
import { useLimitState, useLimitAlertState } from '@state/limit';
import { useFetchingQueryState, useQueries } from '@state/query';
import { formatISO } from 'date-fns';
import { POSTQuery } from '@lib/fetch/query';
import { mapResponseToQuery } from '@lib/map';
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
import type { SearchTermModifier, SearchTermValues, SearchTermModifierStateValue } from '@appTypes/term';
import type { CreateQueryPayload, QueryTerm, Query } from '@appTypes/query';
import type { RefCallback } from '@appTypes/ref';
import type { LimitState, LimitAlertState } from '@state/limit';
import type { FetchingQueryState, QueriesState } from '@state/query';

export type SearchTermStateValues = SearchTermValues & { first?: boolean; };
export type SearchTermModifierMap = { [index: string]: SearchTermModifierStateValue; };
export type SearchTermRefMap = { [index: string]: HTMLInputElement; };

export function QueryBuilder(): ReactElement<FC> {
  const defaultTimezone = useMemo<string>((): string => new Intl.DateTimeFormat().resolvedOptions().timeZone, []);
  const queriesState = useQueries((state: QueriesState): QueriesState => state);
  const fetchingQueryState = useFetchingQueryState((state: FetchingQueryState): FetchingQueryState => state);
  const limitState = useLimitState((state: LimitState): LimitState => state);
  const limitAlertState = useLimitAlertState((state: LimitAlertState): LimitAlertState => state);
  const [submitDisabled, setSubmitDisabled] = useState<boolean>(false);
  const [timezone, setTimezone] = useState<string>(defaultTimezone);
  const [platform, setPlatform] = useState<string>('');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [modifiers, setModifiers] = useState<SearchTermModifierMap>({ default: EQ });
  const searchTermsRef = useRef<SearchTermRefMap>({});
  const isStateEmpty: boolean = (
    (timezone.length === 0 || timezone === defaultTimezone) && platform.length === 0 && startDate == null && endDate == null &&
    Object.keys(modifiers).length === 1 && modifiers['default'].length === 0 &&
    (Object.keys(searchTermsRef.current).length === 0 || searchTermsRef.current['default']?.value.length === 0)
  );
  const isNotSubmittable: boolean = (
    timezone.length === 0 || platform.length === 0 || startDate == null || endDate == null || searchTermsRef.current['default'].value.length === 0 || modifiers['default'].length === 0
  );
  const handleStartDateChange = (date?: Date): void => setStartDate(date || null);
  const handleEndDateChange = (date?: Date): void => setEndDate(date || null);
  const handleTermRefAdd = (id: string): RefCallback => {
    return (ref: HTMLInputElement | null): void => {
      searchTermsRef.current[id] = ref as HTMLInputElement;
    };
  };
  const handleSelectChange = (id: string, value: SearchTermModifier): void => setModifiers((state: SearchTermModifierMap): SearchTermModifierMap => ({
    ...state,
    [id]: value
  }));
  const handleSearchTermDelete = (key: string): void => {
    const { [key]: _, ...refs } = searchTermsRef.current;
    searchTermsRef.current = refs;
    setModifiers((state: SearchTermModifierMap): SearchTermModifierMap => {
      const { [key]: _, ...modifiers } = state;

      return modifiers;
    });
  };
  const handleSearchTermAdd = (): void => {
    setModifiers((state: SearchTermModifierMap): SearchTermModifierMap => ({
      ...state,
      [self.crypto.randomUUID()]: ''
    }));
  };
  const handleClear = (): void => {
    if (timezone.length > 0 && timezone !== defaultTimezone) setTimezone(defaultTimezone);
    if (startDate != null) setStartDate(null);
    if (endDate != null) setEndDate(null);
    if (platform.length > 0) setPlatform('');
    if (Object.keys(modifiers).length > 1 || searchTermsRef.current['default'].value.length > 0 || modifiers['default'].length > 0) {
      setModifiers({ default: EQ });
      searchTermsRef.current = { default: searchTermsRef.current['default'] };
    }
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
      terms: Object.entries(modifiers).map((item: [string, SearchTermModifierStateValue]): QueryTerm => ({
        modifier: item[1] as SearchTermModifier,
        term: searchTermsRef.current[item[0]].value
      })) as Array<QueryTerm>
    };
    const response = await POSTQuery(payload);
    const query: Query = mapResponseToQuery(response.data);

    handleClear();
    fetchingQueryState.setQuery(query);
    queriesState.push(query);
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
                {Object.entries(modifiers).map((item: [string, SearchTermModifierStateValue]): ReactElement<FC> => {
                  const index: string = item[0];
                  const modifier = item[1] as SearchTermModifier;

                  return <SearchTermInput
                    key={index}
                    index={index}
                    disabled={submitDisabled}
                    modifier={modifier}
                    initTermRef={handleTermRefAdd}
                    onSelectChange={handleSelectChange}
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
