export type Timezone = {
  value: string;
  label: string;
};

export type TimezoneGroup = {
  value: string;
  items: Array<Timezone>;
};

// Grouped for the combobox: the region is the group label, the IANA identifier is the
// value sent to the API, and the label is what the user searches against.
export const TIMEZONE_GROUPS: Array<TimezoneGroup> = [
  {
    value: "North America",
    items: [
      { value: "America/New_York", label: "Eastern Standard Time (EST)" },
      { value: "America/Chicago", label: "Central Standard Time (CST)" },
      { value: "America/Denver", label: "Mountain Standard Time (MST)" },
      { value: "America/Los_Angeles", label: "Pacific Standard Time (PST)" },
      { value: "America/Anchorage", label: "Alaska Standard Time (AKST)" },
      { value: "Pacific/Honolulu", label: "Hawaii Standard Time (HST)" },
    ],
  },
  {
    value: "Europe & Africa",
    items: [
      { value: "Europe/London", label: "Greenwich Mean Time (GMT)" },
      { value: "Europe/Paris", label: "Central European Time (CET)" },
      { value: "Europe/Athens", label: "Eastern European Time (EET)" },
      { value: "Europe/Lisbon", label: "Western European Summer Time (WEST)" },
      { value: "Africa/Maputo", label: "Central Africa Time (CAT)" },
      { value: "Africa/Nairobi", label: "East Africa Time (EAT)" },
    ],
  },
  {
    value: "Asia",
    items: [
      { value: "Europe/Moscow", label: "Moscow Time (MSK)" },
      { value: "Asia/Kolkata", label: "India Standard Time (IST)" },
      { value: "Asia/Shanghai", label: "China Standard Time (CST)" },
      { value: "Asia/Tokyo", label: "Japan Standard Time (JST)" },
      { value: "Asia/Seoul", label: "Korea Standard Time (KST)" },
      { value: "Asia/Makassar", label: "Indonesia Central Standard Time (WITA)" },
    ],
  },
  {
    value: "Australia & Pacific",
    items: [
      { value: "Australia/Perth", label: "Australian Western Standard Time (AWST)" },
      { value: "Australia/Adelaide", label: "Australian Central Standard Time (ACST)" },
      { value: "Australia/Sydney", label: "Australian Eastern Standard Time (AEST)" },
      { value: "Pacific/Auckland", label: "New Zealand Standard Time (NZST)" },
      { value: "Pacific/Fiji", label: "Fiji Time (FJT)" },
    ],
  },
  {
    value: "South America",
    items: [
      { value: "America/Argentina/Buenos_Aires", label: "Argentina Time (ART)" },
      { value: "America/La_Paz", label: "Bolivia Time (BOT)" },
      { value: "America/Sao_Paulo", label: "Brasilia Time (BRT)" },
      { value: "America/Santiago", label: "Chile Standard Time (CLT)" },
    ],
  },
];

export const TIMEZONES: Array<Timezone> = TIMEZONE_GROUPS.flatMap(
  (group: TimezoneGroup): Array<Timezone> => group.items
);
