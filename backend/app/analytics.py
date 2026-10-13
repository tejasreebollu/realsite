"""Read-only portal analytics. Stock is current; activity uses India calendar days."""
from collections import Counter
from datetime import datetime, time, timedelta, timezone
from statistics import median
from typing import Literal

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Property, Inquiry, User, Favorite, SavedSearch, AgentProfile

IST = timezone(timedelta(hours=5, minutes=30))


def local_date(value):
    if value.tzinfo is None:  # SQLite stores naive UTC datetimes.
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST).date()


def distribution(values, edges, labels):
    counts = [0] * len(labels)
    for value in values:
        index = next((i for i, edge in enumerate(edges) if value < edge), len(edges))
        counts[index] += 1
    return [{'label': label, 'count': count} for label, count in zip(labels, counts)]


def create_analytics_router(admin_user, database):
    router = APIRouter(prefix='/api/admin', tags=['Administration'])

    @router.get('/analytics')
    def analytics(days: int = Query(30, ge=1, le=365),
                  dataset: Literal['all', 'owner', 'synthetic'] = 'all',
                  user=Depends(admin_user), db: Session = Depends(database)):
        if days not in (30, 90, 365):
            raise HTTPException(422, 'Reporting period must be 30, 90 or 365 days')
        today = datetime.now(IST).date()
        start = today - timedelta(days=days - 1)
        previous_start = start - timedelta(days=days)
        lower = datetime.combine(previous_start, time.min, IST).astimezone(timezone.utc)
        upper = datetime.combine(today + timedelta(days=1), time.min, IST).astimezone(timezone.utc)
        scope = [] if dataset == 'all' else [Property.demo.is_(dataset == 'synthetic')]
        properties = db.execute(select(Property.id, Property.city, Property.kind, Property.purpose,
            Property.price, Property.active, Property.demo, Property.created_at).where(*scope)).all()
        active = [p for p in properties if p.active]
        by_id = {p.id: p for p in properties}
        inquiries = db.execute(select(Inquiry.property_id, Inquiry.created_at)
            .join(Property, Property.id == Inquiry.property_id)
            .where(*scope, Inquiry.created_at >= lower, Inquiry.created_at < upper)).all()
        current = [i for i in inquiries if local_date(i.created_at) >= start]
        previous = len(inquiries) - len(current)
        inquiry_counts = Counter(i.property_id for i in current)
        favorites = Counter(dict(db.execute(select(Favorite.property_id, func.count())
            .join(Property, Property.id == Favorite.property_id).where(*scope)
            .group_by(Favorite.property_id)).all()))
        sale = [p.price for p in active if p.purpose == 'sale']
        rent = [p.price for p in active if p.purpose == 'rent']
        new = sum(start <= local_date(p.created_at) <= today for p in properties)
        old_new = sum(previous_start <= local_date(p.created_at) < start for p in properties)
        users = db.execute(select(User.role, User.active, User.demo, User.created_at)).all()
        applications = Counter(dict(db.execute(select(AgentProfile.status, func.count())
            .group_by(AgentProfile.status)).all()))
        # Daily / weekly buckets start at the selected period's first calendar day.
        bucket_days = 1 if days == 30 else 7 if days == 90 else 30
        series = []
        for offset in range(0, days, bucket_days):
            begin = start + timedelta(days=offset)
            finish = min(begin + timedelta(days=bucket_days - 1), today)
            series.append({'date': begin.isoformat(), 'end': finish.isoformat(),
                'listings': 0, 'inquiries': 0, 'registrations': 0})
        def add_event(date, field):
            if start <= date <= today:
                series[(date - start).days // bucket_days][field] += 1
        for p in properties: add_event(local_date(p.created_at), 'listings')
        for i in current: add_event(local_date(i.created_at), 'inquiries')
        for u in users: add_event(local_date(u.created_at), 'registrations')
        cities = []
        for city in sorted({p.city for p in active} | {by_id[i.property_id].city for i in current}):
            stock = [p for p in active if p.city == city]
            city_sales = [p.price for p in stock if p.purpose == 'sale']
            city_rents = [p.price for p in stock if p.purpose == 'rent']
            leads = sum(by_id[i.property_id].city == city for i in current)
            active_leads = sum(inquiry_counts[p.id] for p in stock)
            cities.append({'city': city, 'active': len(stock), 'sale': len(city_sales), 'rent': len(city_rents),
                'inquiries': leads, 'active_inquiries': active_leads,
                'per_100': round(active_leads / len(stock) * 100, 1) if stock else None,
                'median_sale': median(city_sales) if city_sales else None,
                'median_rent': median(city_rents) if city_rents else None})
        cities.sort(key=lambda c: (-c['inquiries'], -c['active'], c['city']))
        ages = [max(0, (today - local_date(p.created_at)).days) for p in active]
        without_leads = sum(not inquiry_counts[p.id] for p in active)
        signals = []
        if cities and cities[0]['inquiries']:
            city = cities[0]
            signals.append({'title': f"Explore {city['city']}", 'detail':
                f"{city['inquiries']} enquiries in this period. Compare local supply and asking prices before expanding.", 'section': 'properties'})
        else:
            signals.append({'title': 'Establish an enquiry baseline', 'detail':
                'No enquiries in this selection. Review listing visibility and acquisition channels before drawing demand conclusions.', 'section': 'inquiries'})
        signals.append({'title': 'Review listing engagement', 'detail':
            f'{without_leads} of {len(active)} active listings received no enquiries in this period. Review photos, pricing and listing detail.', 'section': 'properties'})
        signals.append({'title': 'Agent onboarding', 'detail':
            f"{applications['pending']} applications await review across the portal. Approved local agents can help expand owner inventory.", 'section': 'agents'})
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'period': {'days': days, 'start': start.isoformat(), 'end': today.isoformat(),
                'previous_start': previous_start.isoformat(), 'previous_end': (start - timedelta(days=1)).isoformat(),
                'bucket_days': bucket_days, 'timezone': 'Asia/Kolkata'}, 'dataset': dataset,
            'summary': {'active': len(active), 'archived': len(properties) - len(active),
                'synthetic': sum(p.demo for p in active), 'owner': sum(not p.demo for p in active),
                'sale': len(sale), 'rent': len(rent), 'new_listings': new, 'previous_new_listings': old_new,
                'inquiries': len(current), 'previous_inquiries': previous,
                'median_sale': median(sale) if sale else None, 'median_rent': median(rent) if rent else None,
                'saved_homes': sum(favorites.values()), 'without_inquiries': without_leads},
            'activity': series, 'cities': cities,
            'types': [{'label': kind, 'count': count} for kind, count in Counter(p.kind for p in active).most_common()],
            'pricing': {'sale': distribution(sale, [5000000, 10000000, 20000000, 50000000],
                ['Under ₹50 L', '₹50 L–1 Cr', '₹1–2 Cr', '₹2–5 Cr', '₹5 Cr+']),
                'rent': distribution(rent, [15000, 30000, 50000, 100000],
                ['Under ₹15K', '₹15–30K', '₹30–50K', '₹50K–1 L', '₹1 L+'])},
            'age': distribution(ages, [31, 91, 181], ['0–30 days', '31–90 days', '91–180 days', '181+ days']),
            'accounts': {'scope': 'Whole portal, all datasets', 'total': len(users),
                'active': sum(u.active for u in users), 'suspended': sum(not u.active for u in users),
                'demo': sum(u.demo for u in users),
                'registrations': sum(start <= local_date(u.created_at) <= today for u in users),
                'roles': [{'label': role.title(), 'count': count} for role, count in Counter(u.role for u in users).most_common()],
                'saved_searches': db.scalar(select(func.count()).select_from(SavedSearch))},
            'agents': [{'label': status.title(), 'count': applications[status]} for status in ['pending', 'approved', 'rejected']],
            'signals': signals,
        }

    return router
