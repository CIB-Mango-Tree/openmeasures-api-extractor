"use client"
import { useState, useEffect, useMemo } from 'react';
import { parse, format, sub } from 'date-fns';
import { ChevronDownIcon } from 'lucide-react';
import { Button } from '@components/ui/button';
import { Calendar } from '@components/ui/calendar';
import { Input } from '@components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import type { ReactElement, FC, ChangeEvent } from 'react';

export interface DateTimePickerProps {
  value: Date | null;
  onChange?: (value: Date) => void;
  disabled?: boolean;
}

export default function DateTimePicker({ value, disabled, onChange }: DateTimePickerProps): ReactElement<FC> {
  const [mounted, setMounted] = useState<boolean>(false);
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState<Date | null>(null);
  const [time, setTime] = useState<string>('00:00:00');
  const cuttoffDate = useMemo<Date>((): Date => sub(new Date(), { months: 6 }), [open]);
  const handleDateSelect = (date?: Date): void => {
    setDate(date || null);
    setOpen(false);
  };
  const handleTimeChange = (event: ChangeEvent<HTMLInputElement>): void => {
    if (event.currentTarget.value.length === 0) {
      setTime('00:00:00');
      return;
    }

    setTime(event.currentTarget.value);
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect((): void => {
    if (value == null && date == null) return;
    if (value == null && date != null) {
      setDate(null);
      setTime('00:00:00');
      return;
    }

    const combinedDateTime: Date = parse(time, 'HH:mm:ss', date as Date);

    if (combinedDateTime.getTime() === value?.getTime()) return;

    setDate(value);
    setTime(format(combinedDateTime, 'HH:mm:ss'));
  }, [value]);

  useEffect((): void => {
    if (onChange == null) return;
    if (date == null || time.length === 0) return;

    const combinedDateTime: Date = parse(time, 'HH:mm:ss', date);

    if (combinedDateTime.getTime() === value?.getTime()) return;

    onChange(combinedDateTime);
  }, [date, time]);

  return (
    <div className="grid grid-flow-col grid-cols-8 gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            id="date-picker"
            disabled={disabled}
            className="font-normal col-span-5 justify-start"
          >
            <span className="w-full text-left">
              {mounted && date != null ? format(date, 'MM/dd/yyyy') : 'Select date'}
            </span>
            <ChevronDownIcon />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto overflow-hidden p-0" align="start">
          <Calendar
            mode="single"
            selected={date != null ? date : undefined}
            captionLayout="dropdown"
            disabled={disabled}
            endMonth={cuttoffDate}
            onSelect={handleDateSelect}
          />
        </PopoverContent>
      </Popover>
      <Input
        type="time"
        step="1"
        autoComplete="off"
        value={time}
        onChange={handleTimeChange}
        disabled={disabled}
        className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none col-span-3"
      />
    </div>
  );
}
