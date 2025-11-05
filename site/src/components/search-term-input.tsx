import { Button } from './ui/button';
import { Field } from '@components/ui/field';
import { Input } from '@components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@components/ui/select';
import { Tooltip, TooltipTrigger, TooltipContent } from '@components/ui/tooltip';
import { Delete } from 'lucide-react';
import { cn } from '@lib/utils';
import { EQ, AND, OR, NOT } from '@constants/modifiers';
import type { ReactElement, FC, ChangeEvent } from 'react';
import type { SearchTermChangeValues, SearchTermModifier } from '@appTypes/term';


export interface SearchTermInputProps {
  index: string;
  modifier: SearchTermModifier | '';
  term: string;
  onChange: (values: SearchTermChangeValues) => void;
  disabled?: boolean;
  onButtonCLick?: (key: string) => void;
};

export default function SearchTermInput({ index, modifier, term, onChange, disabled = false, onButtonCLick }: SearchTermInputProps): ReactElement<FC> {
  const isDefault: boolean = index === 'default';
  const inputClasses: string = cn({
    'w-1/2': isDefault,
    'w-[42.75%]': !isDefault
  });
  const handleSelect = (value: string): void => {
    if (value === modifier) return;
    onChange({
      index,
      term,
      modifier: value as SearchTermModifier
    });
  };
  const handleChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const value = event.currentTarget.value;
    if (value === term) return;

    onChange({
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
          <SelectItem value={EQ}>Contains</SelectItem>
          <SelectItem value={NOT}>Does Not Contain</SelectItem>
          <SelectItem value={AND} disabled={isDefault}>Also Contains</SelectItem>
          <SelectItem value={OR} disabled={isDefault}>Or Contains</SelectItem>
        </SelectContent>
      </Select>
      <Input type="text"
        disabled={disabled}
        placeholder="Type term here.."
        autoComplete="off"
        value={term}
        onChange={handleChange}
        className={inputClasses} />
      {!isDefault && (
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
