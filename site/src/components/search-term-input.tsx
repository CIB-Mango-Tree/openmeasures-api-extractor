import { Button } from './ui/button';
import { Field } from '@components/ui/field';
import { Input } from '@components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@components/ui/select';
import { Tooltip, TooltipTrigger, TooltipContent } from '@components/ui/tooltip';
import { Delete } from 'lucide-react';
import { cn } from '@lib/utils';
import type { ReactElement, FC, ChangeEvent } from 'react';
import type { SearchTermChangeValues, SearchTermModifier } from '@appTypes/term';


export interface SearchTermInputProps {
  index: number;
  modifier: SearchTermModifier | '';
  term: string;
  onChange: (values: SearchTermChangeValues) => void;
  disabled?: boolean;
  showDeleteButton?: boolean;
  onButtonCLick?: (key: number) => void;
};

export default function SearchTermInput({ index, modifier, term, onChange, disabled, showDeleteButton, onButtonCLick }: SearchTermInputProps): ReactElement<FC> {
  const inputClasses: string = cn({
    'w-1/2': !showDeleteButton,
    'w-[42.75%]': showDeleteButton
  });
  const handleSelect = (value: string): void => {
    if (value !== modifier) onChange({
      index,
      term,
      modifier: value as SearchTermModifier
    });
  };
  const handleChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const value = event.currentTarget.value;
    if (value != term) onChange({
      index,
      modifier,
      term: value
    });
  };
  const handleDeleteClick = (): void => {
    if (onButtonCLick != null) onButtonCLick(index);
  };

  return (
    <Field key={index} orientation="horizontal">
      <Select disabled={disabled} value={modifier} onValueChange={handleSelect} >
        <SelectTrigger className="w-1/2">
          <SelectValue placeholder="Select Modifier" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="EQUAL">Contains</SelectItem>
          <SelectItem value="AND">Also Contains</SelectItem>
          <SelectItem value="OR">Or Contains</SelectItem>
        </SelectContent>
      </Select>
      <Input type="text"
        disabled={disabled}
        placeholder="Type term here.."
        autoComplete="off"
        value={term}
        onChange={handleChange}
        className={inputClasses} />
      {showDeleteButton && (
        <Tooltip delayDuration={1000}>
          <TooltipTrigger asChild>
            <Button variant="link" className="cursor-pointer" disabled={disabled} onClick={handleDeleteClick}>
              <Delete className="size-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Remove search term
          </TooltipContent>
        </Tooltip>
      )}
    </Field>
  );
}
