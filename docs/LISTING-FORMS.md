# Listing properties, open plots and rentals

Updated: 11 October 2026.

Open **Sell** or **Manage listings → Add a listing**. One regular account can buy, rent and publish listings.

| Form | Supported property | Specific information |
| --- | --- | --- |
| Sell a property | Apartment, villa, house, building, commercial building, office, shop | Selling price, built-up area, residential bedroom/bathroom counts and amenities |
| Sell an open plot | Residential, commercial or agricultural land | Area in square feet, square yards or acres; optional facing, road width and owner-supplied layout/authority approval |
| Rent a property | All residential and commercial types above | Monthly rent, deposit, furnishing and optional availability date |

Commercial forms omit bedrooms and make bathrooms optional. Plots omit bedrooms and bathrooms and support sale. Each form follows **Details → Location → Photos → Review**. Back retains entries; editing opens the appropriate form with existing photos and location.

## Map location

Enter the city, state, address and PIN code. Suggestions cover the five demo cities; another Indian city can be typed. Select the property entrance by clicking the map, dragging the pin, using your device location, or panning and choosing **Place pin at map centre**. Fine-tune buttons support keyboard users. Coordinates are saved automatically.

Device location asks for permission when its button is clicked. Map tiles need internet access; a pin can still be selected if tiles fail. The owner is responsible for the position.

## Image uploads

Choose or drag multiple **JPEG, PNG or WebP** images, up to **10 per listing** and **5 MB each**. Previews and progress appear immediately. Remove photos or choose **Make cover**; at least one photo is required.

Authenticated uploads check actual image contents and decoded dimensions, apply camera orientation, strip metadata and produce a JPEG up to 2400 pixels per edge. Random filenames avoid using original names. Images can only be attached by their uploading account, and listing photos are publicly served through /api/uploads/{id}.jpg. Existing hosted HTTPS photos and sample image paths continue working on older listings.

Image metadata is in PostgreSQL; files persist in the property_images Docker volume mounted at /app/uploads. Restarting or rebuilding retains them. Back up this volume with PostgreSQL. Photos from abandoned drafts or removed from a form remain stored; automated cleanup and managed Azure Blob storage remain future work. The Azure VM overlay inherits the local image volume.

## Discovery and details

**Open plots** in the main navigation opens plot search. Property-type filters include all residential/commercial types and plots; plot/commercial searches omit bedroom filters. Cards, maps, favourites and enquiries support all types.

Plots show land area, use, facing, road width and owner-supplied approval without fictitious bedroom counts. Rental details show deposit, furnishing and availability. Plot areas retain their entered units and are normalised to square feet for sorting and minimum-area search. Approval text is supplied by the owner and is not independently verified.

The original 100 synthetic homes are preserved. Additional owner properties and plots do not replace those samples.

## Optional details for India search

Expand **More property details (optional)** in Details to supply listing source/status, maintenance, possession, ownership, parking, carpet/attached-plot area, construction year, storeys, basement, senior-living status, views, RERA number and HTTPS tour links. Fields adapt to property sale, open plots and rentals. Sale properties can now specify furnishing too. Leave unknown values blank. Carpet area cannot exceed built-up area. The core four-step form and image/location workflow stay the same.

These values power the [More Filters panel](MORE-FILTERS.md) and appear in property facts. Owner-supplied registrations and approval text are not independent verification. Price changes automatically track the previous asking price for the Price reduced filter. Older API editors that omit the new details preserve them.

## Search and handoff

Listings created through these forms participate in price, room, India More Filters, viewport and [drawn-area search](DRAW-SEARCH.md). Drawing filters the saved map location; it does not change a listing location. Plot and commercial searches hide room-count controls. A supplied 3D tour URL links to content; the built-in sample model is illustrative. See [testing](TESTING.md) for form checks and [handoff](HANDOFF.md) for backing up uploaded images alongside the database.

## Account profiles and reviewed agents

A user and an approved agent use the same listing permissions: both manage only their own properties. Agent approval publishes professional details; it does not independently verify listings or grant administrator permissions. Profile photos and account details are edited through the header avatar, separately from listing photos and property facts. See [user management](USER-MANAGEMENT.md).

In search, hovering a listing card gives its matching map pin a thin cyan glow. Pins stay visible while drawing a boundary, and Apply filters by the saved property coordinates. Suspension revokes the owner's access but preserves listing records; an administrator archives any listings that should also disappear.
