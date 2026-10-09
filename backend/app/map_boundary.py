"""Validated simple polygon search, shared by PostgreSQL and isolated SQLite tests.
Coordinates use Leaflet order: [latitude, longitude]. No schema change is needed.
"""
import json
import math
from functools import lru_cache
from fastapi import HTTPException
from sqlalchemy import and_, case, func, or_
from .models import Property

MAX_VERTICES = 64
EPS = 1e-10

def cross(a, b, c):
    return (b[1]-a[1])*(c[0]-a[0])-(b[0]-a[0])*(c[1]-a[1])

def on_segment(a, b, c):
    return abs(cross(a,b,c)) <= EPS and all(min(a[k],b[k])-EPS <= c[k] <= max(a[k],b[k])+EPS for k in (0,1))

def intersects(a,b,c,d):
    x,y,z,w = cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    return (x*y < 0 and z*w < 0) or any((on_segment(a,b,c),on_segment(a,b,d),on_segment(c,d,a),on_segment(c,d,b)))

@lru_cache(maxsize=128)
def parse_boundary(value):
    if not value:
        return ()
    try:
        points=json.loads(value)
        if not isinstance(points,list) or not 3 <= len(points) <= MAX_VERTICES+1:
            raise ValueError()
        for p in points:
            if not isinstance(p,list) or len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p):
                raise ValueError()
            if not -90 <= p[0] <= 90 or not -180 <= p[1] <= 180:
                raise ValueError()
        if points[0]==points[-1]:
            points=points[:-1]
        if not 3 <= len(points) <= MAX_VERTICES or len({tuple(p) for p in points})!=len(points):
            raise ValueError()
        if abs(sum(a[1]*b[0]-b[1]*a[0] for a,b in zip(points,points[1:]+points[:1]))) <= EPS:
            raise ValueError()
        edges=list(zip(points,points[1:]+points[:1]))
        for i,(a,b) in enumerate(edges):
            for j,(c,d) in enumerate(edges):
                if j <= i+1 or (i==0 and j==len(edges)-1):
                    continue
                if intersects(a,b,c,d):
                    raise ValueError()
        return tuple(tuple(p) for p in points)
    except (ValueError,TypeError,OverflowError):
        raise HTTPException(422, 'Draw a simple area with 3 to 64 corners. The boundary must not cross itself.')

def apply_boundary(query, value):
    points=parse_boundary(value)
    if not points:
        return query
    lat,lng=Property.lat,Property.lng
    query=query.where(lat.between(min(p[0] for p in points)-EPS,max(p[0] for p in points)+EPS),lng.between(min(p[1] for p in points)-EPS,max(p[1] for p in points)+EPS))
    edges=list(zip(points,points[1:]+points[:1]))
    crossings=[];boundary=[]
    for (y1,x1),(y2,x2) in edges:
        determinant=(x2-x1)*(lat-y1)-(y2-y1)*(lng-x1)
        boundary.append(and_(func.abs(determinant)<=EPS,lat.between(min(y1,y2)-EPS,max(y1,y2)+EPS),lng.between(min(x1,x2)-EPS,max(x1,x2)+EPS)))
        if y1 != y2:
            crosses=and_(or_(and_(lat>=y1,lat<y2),and_(lat>=y2,lat<y1)),lng < x1+(lat-y1)*((x2-x1)/(y2-y1)))
            crossings.append(case((crosses,1),else_=0))
    # The even/odd rule handles concave polygons; edge points are included.
    return query.where(or_(sum(crossings)%2==1,*boundary))
