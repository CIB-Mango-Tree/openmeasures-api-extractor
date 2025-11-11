import { Button } from './ui/button';
import { Field } from '@components/ui/field';
import { Input } from '@components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@components/ui/select';
import { Tooltip, TooltipTrigger, TooltipContent } from '@components/ui/tooltip';
import { Delete } from 'lucide-react';
import { cn } from '@lib/utils';
import { EQ, AND, OR, NOT } from '@constants/modifiers';
import type { ReactElement, FC } from 'react';
import type { SearchTermModifier } from '@appTypes/term';
import type { RefCallback } from '@appTypes/ref';


export interface SearchTermInputProps {
  index: string;
  modifier: SearchTermModifier | '';
  disabled?: boolean;
  onButtonCLick?: (key: string) => void;
  initTermRef: (id: string) => RefCallback;
  onSelectChange: (id: string, value: SearchTermModifier) => void;
};

export default function SearchTermInput({ index, modifier, initTermRef, onSelectChange, onButtonCLick, disabled = false }: SearchTermInputProps): ReactElement<FC> {
  const isDefault: boolean = index === 'default';
  const inputClasses: string = cn({
    'w-1/2': isDefault,
    'w-[42.75%]': !isDefault
  });
  const handleSelect = (value: string): void => {
    if (value === modifier) return;
    onSelectChange(index, value as SearchTermModifier);
  };
  const handleDeleteClick = (): void => {
    if (onButtonCLick != null) onButtonCLick(index);
  };

  return (
    <Field key={index} orientation="horizontal">
      <Select disabled={disabled} value={modifier} onValueChange={handleSelect}>
        <SelectTrigger className="w-1/2">
          <SelectValue placeholder="Select Modifier" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={EQ} disabled={!isDefault}>Contains</SelectItem>
          <SelectItem value={NOT}>Does Not Contain</SelectItem>
          <SelectItem value={AND} disabled={isDefault}>Also Contains</SelectItem>
          <SelectItem value={OR} disabled={isDefault}>Or Contains</SelectItem>
        </SelectContent>
      </Select>
      <Input type="text"
        ref={initTermRef(index)}
        disabled={disabled}
        defaultValue=""
        placeholder="Type term here.."
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
