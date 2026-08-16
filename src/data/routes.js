// Published schedule data transcribed from the supplied Bus-Routes-2026-27.pdf.
// This is source data, not AI/ML output.
export const routeSchedule = {
  source: '/Bus-Routes-2026-27.pdf',
  academicYear: '2026-27', totalPublishedRoutes: 127, destination: 'Punjab Campus',
  featuredRoutes: [
    { id: '01', area: 'Chandigarh / New Chandigarh', firstStop: 'Barrier (Naya Gaon)', departure: '7:30 AM', stops: 8, via: 'Zirakpur - Toll Plaza - Banur', arrival: '8:45 AM' },
    { id: '16', area: 'Chandigarh / New Chandigarh', firstStop: 'Omaxe Extension', departure: '7:10 AM', stops: 7, via: 'Zirakpur - Toll Plaza - Banur', arrival: '8:45 AM' },
    { id: '21', area: 'Mohali / Kharar / Kurali', firstStop: 'Phase 07 Lights', departure: '7:40 AM', stops: 8, via: 'Raipur - Landran Banur Road', arrival: '8:45 AM' },
    { id: '47', area: 'Panchkula / Mani Majra / Dhakoli', firstStop: 'Pankaj Masala', departure: '7:50 AM', stops: 5, via: 'Zirakpur - Toll Plaza - Banur', arrival: '8:45 AM' },
    { id: '64', area: 'Patiala', firstStop: 'Police Line', departure: '7:40 AM', stops: 3, via: 'Toll Plaza - Rajpur By Pass', arrival: '8:45 AM' },
    { id: '87', area: 'Pipli / Shahbad / Saha', firstStop: 'Shahbad Bus Stand', departure: '7:15 AM', stops: 3, via: 'Shambhu Toll Plaza - Gagan Chowk (Raj)', arrival: '8:45 AM' },
    { id: '107', area: 'Rajpura', firstStop: 'Savita Hospital', departure: '7:50 AM', stops: 11, via: 'Gagan Chowk (Raj)', arrival: '8:45 AM' },
    { id: '113', area: 'Zirakpur / Behlana', firstStop: 'Behlana (Airforce Chowk)', departure: '7:55 AM', stops: 5, via: 'Zirakpur - Toll Plaza - Banur', arrival: '8:45 AM' },
    { id: '121', area: 'Sirhind / Bassi Pathana', firstStop: '4 No Chungi', departure: '7:45 AM', stops: 6, via: 'Rajpura / Ludhiana Highway', arrival: '8:45 AM' },
    { id: '127', area: 'Khanna', firstStop: 'Gobindgarh Bus Stand', departure: '7:45 AM', stops: 3, via: 'Rajpura / Ludhiana Highway', arrival: '8:45 AM' },
  ],
};

// Page index for every route identifier published in the supplied schedule.
// Selecting a route in the UI loads this exact source page, including all stops and times.
const routePageGroups = [
  [1, '01 02 03'], [2, '04 05 06 07'], [3, '08 09 10 11'], [4, '12 13 14'], [5, '15 16'],
  [6, '21 22 23'], [7, '24 25 26'], [8, '27 28 29 30 31'], [9, '32 33 34'], [10, '36 37 38 39 40'],
  [11, '41 42 43 44'], [12, '45 46 47 48'], [13, '49 50 51 52'], [14, '53 54'], [15, '55 60 61 62'],
  [16, '64 65 66 67'], [17, '68 69 70 71'], [18, '72 73 74 75 76'], [19, '77 78 79 80'], [20, '81 82 83 84 85'],
  [21, '86 89 90'], [22, '92 93 94 95'], [23, '96 97 98 99'], [24, '100 101 102 103'], [25, '87 88 125'],
  [26, '107'], [27, '110 111 112'], [28, '113 114'], [29, '115 116 117'], [30, '121 124'], [31, '122 123 126 127'],
];

export const routePages = Object.fromEntries(
  routePageGroups.flatMap(([page, routeIds]) => routeIds.split(' ').map((id) => [id, page])),
);

export const allRouteIds = Object.keys(routePages).sort((first, second) => Number(first) - Number(second));
