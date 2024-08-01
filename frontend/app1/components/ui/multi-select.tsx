"use client";

import { useState, forwardRef, ElementRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const MultiSelect = forwardRef<ElementRef<"div">, MultiSelectProps>(
  ({ options, selected, onChange, placeholder = "Select options...", className, style }, ref) => {
    const [open, setOpen] = useState(false);

    const handleSelect = (value: string) => {
      if (selected.includes(value)) {
        onChange(selected.filter((item) => item !== value));
      } else {
        onChange([...selected, value]);
      }
    };

    const handleRemove = (value: string) => {
      onChange(selected.filter((item) => item !== value));
    };

    const handleSelectAll = () => {
      onChange(options.map(option => option.value));
    };

    const handleSelectAllLabel = () => {
      if (selected.length === 0) {
        onChange(options.map(option => option.value));
      } else {
        onChange([]);
      }
    };

    const handleClear = () => {
      onChange([]);
    };

    return (
      <div ref={ref} className={cn("space-y-2", className)} style={style}>
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={open}
              className="w-full justify-between bg-background hover:bg-background min-h-[40px] h-auto py-2"
            >
              <div className="flex flex-wrap gap-1">
                {selected.length === 0 ? (
                  <span className="text-muted-foreground">{placeholder}</span>
                ) : selected.length === options.length ? (
                  <div className="flex items-center bg-secondary px-2 py-1 rounded-sm">
                    <span>All {options.length === 1 ? options[0].label : 'Options'}</span>
                    <button
                      type="button"
                      className="ml-1 rounded-full hover:bg-secondary/80"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectAllLabel();
                      }}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ) : (
                  selected.map((value) => {
                    const option = options.find((opt) => opt.value === value);
                    return (
                      <Badge key={value} variant="secondary" className="mr-1 mb-1">
                        {option?.label || value}
                        <button
                          type="button"
                          className="ml-1 rounded-full hover:bg-foreground/10"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemove(value);
                          }}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    );
                  })
                )}
              </div>
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-full p-0 z-50 border border-border bg-popover shadow-md">
            <Command>
              <CommandList className="max-h-60">
                <CommandGroup className="p-1">
                  {options.map((option) => (
                    <CommandItem
                      key={option.value}
                      onSelect={() => handleSelect(option.value)}
                      className="cursor-pointer px-2 py-2 text-sm rounded-sm hover:bg-accent"
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          selected.includes(option.value) ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {option.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
              <div className="p-2 border-t border-border flex justify-between">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSelectAll}
                  className="text-xs hover:bg-accent"
                >
                  Select All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClear}
                  className="text-xs hover:bg-accent"
                >
                  Clear
                </Button>
              </div>
            </Command>
          </PopoverContent>
        </Popover>
      </div>
    );
  }
);

MultiSelect.displayName = "MultiSelect";