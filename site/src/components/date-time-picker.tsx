"use client"
import { useState, useEffect } from 'react';
import { ChevronDownIcon } from 'lucide-react';
import { parse, format } from 'date-fns';
import { Button } from '@components/ui/button';
import { Calendar } from '@components/ui/calendar';
import { Input } from '@components/ui/input';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import type { ReactElement, FC, ChangeEvent } from 'react';

export interface DateTimePickerProps {
  value?: Date;
  onChange?: (value: Date) => void;
}

export default function DateTimePicker({ value, onChange }: DateTimePickerProps): ReactElement<FC> {
  const [mounted, setMounted] = useState<boolean>(false);
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [time, setTime] = useState<string>('00:00:00');
  const handleDateSelect = (date?: Date): void => {
    setDate(date);
    setOpen(false);
  };
  const handleTimeChange = (event: ChangeEvent<HTMLInputElement>): void => {
    if (event.currentTarget.value.length === 0) {
      setTime('00:00:00');
      return;
    }

    console.log(event.currentTarget.value);

    setTime(event.currentTarget.value);
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect((): void => {
    if (value == null && date == null) return;
    if (value == null && date != null) {
      setDate(undefined);
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
            selected={date}
            captionLayout="dropdown"
            onSelect={handleDateSelect}
          />
        </PopoverContent>
      </Popover>
      <Input
        type="time"
        step="1"
        value={time}
        onChange={handleTimeChange}
        className="bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none col-span-3"
      />
    </div>
  );
}
