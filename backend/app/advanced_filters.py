"""India listing attributes and reusable SQL predicates for advanced search."""
import re
import math
from datetime import datetime, timedelta, timezone
from typing import Literal
from urllib.parse import urlsplit
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import String, case, func, or_
from .models import Property

AMENITIES = ['Parking', 'Security', 'Power backup', 'Balcony', 'Swimming pool', 'Gym', 'Garden', 'Water supply', 'Electricity', 'Boundary wall', 'Gated community', 'Lift', 'Air conditioning']
DIRECTIONS = ['', 'North', 'South', 'East', 'West', 'North-East', 'North-West', 'South-East', 'South-West']

def selections(values):
    choices = '|'.join(re.escape(v) for v in values)
    return Field(default='', max_length=400, pattern=rf'^(?:none|(?:{choices})(?:,(?:{choices}))*)?$')

class AdvancedFilters(BaseModel):
    max_maintenance: int | None = Field(default=None, ge=0, le=1_000_000)
    posted_by: str = selections(['Owner', 'Broker', 'Builder'])
    sale_type: str = selections(['Resale', 'New project', 'Bank auction'])
    listing_status: str = selections(['Available', 'Coming soon', 'Under offer'])
    possession: Literal['', 'Ready to move', 'Under construction'] = ''
    furnishing_filter: Literal['', 'Unfurnished', 'Semi-furnished', 'Furnished'] = ''
    ownership: Literal['', 'Freehold', 'Leasehold'] = ''
    rera_only: bool = False
    site_visit: bool = False
    tour_3d: bool = False
    video_tour: bool = False
    min_parking: int = Field(default=0, ge=0, le=20)
    covered_parking: bool = False
    max_sqft: int | None = Field(default=None, ge=0, le=10_000_000)
    min_carpet: int = Field(default=0, ge=0, le=10_000_000)
    max_carpet: int | None = Field(default=None, ge=0, le=10_000_000)
    min_plot: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)
    max_plot: float | None = Field(default=None, ge=0, le=10_000_000, allow_inf_nan=False)
    plot_unit: Literal['sqft', 'sqyd', 'acre'] = 'sqyd'
    plot_use_filter: Literal['', 'Residential', 'Commercial', 'Agricultural'] = ''
    approval_only: bool = False
    min_road_width: int = Field(default=0, ge=0, le=300)
    year_min: int | None = Field(default=None, ge=1800, le=2100)
    year_max: int | None = Field(default=None, ge=1800, le=2100)
    basement: bool = False
    single_storey: bool = False
    senior_living: Literal['include', 'exclude', 'only'] = 'include'
    amenities_all: str = selections(AMENITIES)
    views: str = selections(['City', 'Hills', 'Park', 'Water'])
    facing: Literal['', 'North', 'South', 'East', 'West', 'North-East', 'North-West', 'South-East', 'South-West'] = ''
    radius_lat: float | None = Field(default=None, ge=6, le=38)
    radius_lng: float | None = Field(default=None, ge=68, le=98)
    radius_km: int = Field(default=0, ge=0, le=100)
    price_reduced: bool = False
    days_listed: int = Field(default=0, ge=0, le=365)
    keywords: str = Field(default='', max_length=150)

class PropertyFeatures(BaseModel):
    model_config = ConfigDict(extra='forbid')
    posted_by: Literal['', 'Owner', 'Broker', 'Builder'] = 'Owner'
    listing_status: Literal['', 'Available', 'Coming soon', 'Under offer'] = 'Available'
    sale_type: Literal['', 'Resale', 'New project', 'Bank auction'] = ''
    possession: Literal['', 'Ready to move', 'Under construction'] = ''
    ownership: Literal['', 'Freehold', 'Leasehold'] = ''
    maintenance: int | None = Field(default=None, ge=0, le=1_000_000)
    parking: int | None = Field(default=None, ge=0, le=20)
    covered_parking: bool | None = None
    carpet_sqft: int | None = Field(default=None, gt=0, le=10_000_000)
    plot_sqft: int | None = Field(default=None, gt=0, le=10_000_000)
    year_built: int | None = Field(default=None, ge=1800, le=2100)
    floors: int | None = Field(default=None, ge=1, le=100)
    basement: bool | None = None
    senior_living: bool | None = None
    facing: Literal['', 'North', 'South', 'East', 'West', 'North-East', 'North-West', 'South-East', 'South-West'] = ''
    views: list[Literal['City', 'Hills', 'Park', 'Water']] = Field(default_factory=list, max_length=4)
    site_visit: bool | None = None
    tour_3d_url: str = Field(default='', max_length=2000)
    video_url: str = Field(default='', max_length=2000)
    rera_id: str = Field(default='', max_length=100)

    @field_validator('rera_id')
    @classmethod
    def trim_registration(cls, value):
        return value.strip()

    @field_validator('tour_3d_url', 'video_url')
    @classmethod
    def safe_tour_url(cls, value):
        value = value.strip()
        if not value:
            return ''
        # The illustrative sample model is a safe local asset.
        if value == '/tours/demo-3d.html':
            return value
        parts = urlsplit(value)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            raise ValueError('Tour links must be HTTPS URLs')
        return value


def validate_advanced(filters):
    for low, high, name in [(filters.min_sqft, filters.max_sqft, 'Property area'), (filters.min_carpet, filters.max_carpet, 'Carpet area'), (filters.min_plot, filters.max_plot, 'Plot area'), (filters.year_min, filters.year_max, 'Year built')]:
        if low is not None and high is not None and low > high:
            raise HTTPException(422, name + ': maximum must be at least minimum')
    if filters.radius_km and (filters.radius_lat is None or filters.radius_lng is None):
        raise HTTPException(422, 'Select a map location for the distance filter')


def apply_advanced(query, f):
    feature = Property.features
    for key in ['posted_by', 'sale_type', 'listing_status']:
        value = getattr(f, key)
        if value == 'none':
            query = query.where(False)
        elif value:
            query = query.where(feature[key].as_string().in_(value.split(',')))
    for key in ['possession', 'ownership']:
        if getattr(f, key):
            query = query.where(feature[key].as_string() == getattr(f, key))
    if f.furnishing_filter:
        query = query.where(Property.kind != 'Open Plot', Property.furnishing == f.furnishing_filter)
    if f.max_maintenance is not None:
        query = query.where(feature['maintenance'].as_integer() <= f.max_maintenance)
    if f.min_parking:
        query = query.where(feature['parking'].as_integer() >= f.min_parking)
    for key in ['covered_parking', 'site_visit', 'basement']:
        if getattr(f, key):
            query = query.where(feature[key].as_boolean().is_(True))
    if f.single_storey:
        query = query.where(feature['floors'].as_integer() == 1)
    if f.senior_living != 'include':
        predicate = feature['senior_living'].as_boolean()
        query = query.where(predicate.is_(True) if f.senior_living == 'only' else predicate.is_not(True))
    for selected, key in [(f.tour_3d, 'tour_3d_url'), (f.video_tour, 'video_url'), (f.rera_only, 'rera_id')]:
        if selected:
            query = query.where(feature[key].as_string().is_not(None), feature[key].as_string() != '')
    if f.max_sqft is not None:
        query = query.where(Property.sqft <= f.max_sqft)
    for low, high, column in [(f.min_carpet, f.max_carpet, feature['carpet_sqft'].as_integer()), (f.year_min, f.year_max, feature['year_built'].as_integer())]:
        if low:
            query = query.where(column >= low)
        if high is not None:
            query = query.where(column <= high)
    plot_area = case((Property.kind == 'Open Plot', Property.sqft), else_=feature['plot_sqft'].as_integer())
    factor = {'sqft': 1, 'sqyd': 9, 'acre': 43560}[f.plot_unit]
    if f.min_plot:
        query = query.where(plot_area >= f.min_plot * factor)
    if f.max_plot is not None:
        query = query.where(plot_area <= f.max_plot * factor)
    if f.plot_use_filter:
        query = query.where(Property.kind == 'Open Plot', Property.plot_use == f.plot_use_filter)
    if f.approval_only:
        query = query.where(Property.kind == 'Open Plot', func.trim(Property.plot_approval) != '')
    if f.min_road_width:
        query = query.where(Property.kind == 'Open Plot', Property.road_width_ft >= f.min_road_width)
    if f.facing:
        query = query.where(case((Property.kind == 'Open Plot', Property.plot_facing), else_=feature['facing'].as_string()) == f.facing)
    if f.amenities_all == 'none' or f.views == 'none':
        query = query.where(False)
    else:
        for name in f.amenities_all.split(',') if f.amenities_all else []:
            query = query.where(Property.amenities.cast(String).like(f'%"{name}"%'))
        if f.views:
            query = query.where(or_(*[feature['views'].cast(String).like(f'%"{name}"%') for name in f.views.split(',')]))
    if f.radius_km:
        lat, lng = func.radians(Property.lat), func.radians(Property.lng)
        origin_lat, origin_lng = math.radians(f.radius_lat), math.radians(f.radius_lng)
        h = func.pow(func.sin((lat-origin_lat)/2), 2) + func.cos(lat)*math.cos(origin_lat)*func.pow(func.sin((lng-origin_lng)/2), 2)
        distance = 12742 * func.asin(func.sqrt(case((h > 1, 1), else_=h)))
        query = query.where(distance <= f.radius_km)
    if f.price_reduced:
        query = query.where(Property.previous_price > Property.price)
    if f.days_listed:
        query = query.where(Property.created_at >= datetime.now(timezone.utc) - timedelta(days=f.days_listed))
    if f.keywords.strip():
        text = f.keywords.strip()
        escaped = text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        conditions = [column.ilike('%' + escaped + '%', escape='\\') for column in [Property.title, Property.address, Property.description, Property.plot_approval]]
        reference = re.fullmatch(r'IN-(\d+)', text.upper())
        if reference:
            conditions.append(Property.id == int(reference[1]))
        query = query.where(or_(*conditions))
    return query
