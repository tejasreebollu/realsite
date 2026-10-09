export const amenityOptions = ['Parking', 'Security', 'Power backup', 'Balcony', 'Swimming pool', 'Gym', 'Garden', 'Water supply', 'Electricity', 'Boundary wall', 'Gated community', 'Lift', 'Air conditioning'];
export const directions = ['North', 'South', 'East', 'West', 'North-East', 'North-West', 'South-East', 'South-West'];
export const postedOptions = ['Owner', 'Broker', 'Builder'];
export const saleOptions = ['Resale', 'New project', 'Bank auction'];
export const statusOptions = ['Available', 'Coming soon', 'Under offer'];
export const viewOptions = ['City', 'Hills', 'Park', 'Water'];
export const moreDefaults = {
  max_maintenance: '', posted_by: '', sale_type: '', listing_status: '', possession: '', furnishing_filter: '', ownership: '', rera_only: false,
  site_visit: false, tour_3d: false, video_tour: false, min_parking: 0, covered_parking: false,
  max_sqft: '', min_carpet: 0, max_carpet: '', min_plot: 0, max_plot: '', plot_unit: 'sqyd', plot_use_filter:'', approval_only:false, min_road_width:0, year_min: '', year_max: '',
  basement: false, single_storey: false, senior_living: 'include', amenities_all: '', views: '', facing: '',
  radius_lat: '', radius_lng: '', radius_km: 0, price_reduced: false, days_listed: 0, keywords: '',
};
export const numberMore = ['max_maintenance', 'min_parking', 'max_sqft', 'min_carpet', 'max_carpet', 'min_plot', 'max_plot', 'year_min', 'year_max', 'radius_lat', 'radius_lng', 'radius_km', 'days_listed', 'min_road_width'];
export const booleanMore = ['rera_only', 'site_visit', 'tour_3d', 'video_tour', 'covered_parking', 'basement', 'single_storey', 'price_reduced', 'approval_only'];
export const moreKeys = [...Object.keys(moreDefaults).filter(k => !['plot_unit', 'radius_lat', 'radius_lng'].includes(k)), 'kind', 'min_sqft', 'amenity'];
export function moreCount(filters) {
  return moreKeys.filter(key => {
    const value = filters[key], fallback = moreDefaults[key] ?? (key === 'min_sqft' ? 0 : '');
    return value != null && value !== '' && String(value) !== String(fallback);
  }).length;
}

export function typeFilterReset(kind) {
  return kind === 'Open Plot' ? {beds:0,baths:0,min_sqft:0,max_sqft:'',min_carpet:0,max_carpet:'',year_min:'',year_max:'',min_parking:0,covered_parking:false,basement:false,single_storey:false,senior_living:'include',possession:'',furnishing_filter:'',tour_3d:false,video_tour:false,amenity:'',amenities_all:''} : {plot_use_filter:'',approval_only:false,min_road_width:0,...(['Commercial Building','Office','Shop'].includes(kind) ? {beds:0,baths:0} : {})};
}
