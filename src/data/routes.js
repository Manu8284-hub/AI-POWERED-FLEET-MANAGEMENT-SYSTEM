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

export const allRouteIds = Array.from(
  { length: routeSchedule.totalPublishedRoutes },
  (_, index) => String(index + 1).padStart(2, '0'),
);
