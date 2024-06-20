"use client";

import React from "react";
import ReactDatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface DatePickerProps {
  date: Date | undefined;
  setDate: (date: Date | undefined) => void;
  minDate?: Date;
  placeholder?: string;
  className?: string;
}

export function DatePicker({
  date,
  setDate,
  minDate,
  placeholder = "Pick a date",
  className
}: DatePickerProps) {
  return (
    <div className={cn("relative", className)}>
      <ReactDatePicker
        selected={date}
        onChange={(date: Date | null) => setDate(date || undefined)}
        showDateSelect
        dateFormat="PPP"
        minDate={minDate}
        placeholderText={placeholder}
        className="w-full rounded-md border border-input bg-input px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      />
      <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none">
        <CalendarIcon className="h-4 w-4" />
      </div>
    </div>
  );
}

interface DateTimePickerProps {
  date: Date | undefined;
  setDate: (date: Date | undefined) => void;
  minDate?: Date;
  placeholder?: string;
  className?: string;
}

export function DateTimePicker({
  date,
  setDate,
  minDate,
  placeholder = "Pick a date and time",
  className
}: DateTimePickerProps) {
  return (
    <div className={cn("relative", className)}>
      <ReactDatePicker
        selected={date}
        onChange={(date: Date | null) => setDate(date || undefined)}
        showTimeSelect
        timeFormat="HH:mm"
        timeIntervals={15}
        timeCaption="Time"
        dateFormat="PPP HH:mm"
        minDate={minDate}
        placeholderText={placeholder}
        className="w-full rounded-md border border-input bg-input px-3 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      />
      <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none">
        <CalendarIcon className="h-4 w-4" />
      </div>
    </div>
  );
}