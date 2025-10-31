import { useState } from 'react';
import { SquarePlus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent } from '@components/ui/card';
import { Field, FieldLabel, FieldSet, FieldGroup } from '@components/ui/field';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@components/ui/select';
import { Button } from '@components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@components/ui/tooltip';
import DateTimePicker from '@components/date-time-picker';
import SearchTermInput from '@components/search-term-input';
import type { ReactElement, FC, FormEvent } from 'react';
import type { SearchTermValues, SearchTermChangeValues } from '@appTypes/term';

export type SearchTermMap = { [index: number]: SearchTermValues; };

export function QueryBuilder(): ReactElement<FC> {
  const [submitDisabled, setSubmitDisabled] = useState<boolean>(false);
  const [timezone, setTimezone] = useState<string>('');
  const [platform, setPlatform] = useState<string>('');
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [searchTerms, setSearchTerms] = useState<SearchTermMap>({
    0: { modifier: 'EQUAL', term: '' }
  });
  const isStateEmpty: boolean = (
    timezone.length === 0 && platform.length === 0 && startDate == null && endDate == null &&
    Object.keys(searchTerms).length === 1 && searchTerms[0].term.length === 0
  );
  const handleStartDateChange = (date?: Date): void => setStartDate(date);
  const handleEndDateChange = (date?: Date): void => setEndDate(date);
  const handleSearchTermChange = (changeValues: SearchTermChangeValues): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => ({
      ...state,
      [changeValues.index]: { modifier: changeValues.modifier, term: changeValues.term }
    }));
  };
  const handleSearchTermDelete = (key: number): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => {
      const { [key]: _, ...terms } = state;

      return terms;
    });
  };
  const handleSearchTermAdd = (): void => {
    setSearchTerms((state: SearchTermMap): SearchTermMap => {
      const maxKey: number = Math.max(...Object.keys(state).map(Number)) + 1;

      return {
        ...state,
        [maxKey]: { modifier: '', term: '' }
      };
    });
  };
  const handleClear = (): void => {
    if (timezone.length > 0) setTimezone('');
    if (startDate != null) setStartDate(undefined);
    if (endDate != null) setEndDate(undefined);
    if (platform.length > 0) setPlatform('');
    if (Object.keys(searchTerms).length > 1 || searchTerms[0].term.length > 0) setSearchTerms({
      0: { modifier: 'EQUAL', term: '' }
    });
  };
  const handleSubmit = (event: FormEvent): void => {
    event.preventDefault();
    setSubmitDisabled(true);
  };

  return (
    <Card className="col-span-8">
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
                  const index: number = parseInt(item[0]);
                  const entry: SearchTermValues = item[1];

                  if (index === 0) return <SearchTermInput
                    key={index}
                    index={index}
                    disabled={submitDisabled}
                    modifier={entry.modifier}
                    term={entry.term}
                    onChange={handleSearchTermChange} />;

                  return <SearchTermInput
                    key={index}
                    index={index}
                    disabled={submitDisabled}
                    modifier={entry.modifier}
                    term={entry.term}
                    onChange={handleSearchTermChange}
                    onButtonCLick={handleSearchTermDelete}
                    showDeleteButton />;
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
              <Button type="submit" className="cursor-pointer" disabled={submitDisabled}>
                Apply
              </Button>
            </Field>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
