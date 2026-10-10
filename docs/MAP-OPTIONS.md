# Map Options

Updated: 11 October 2026.

Open a Buy or Rent search and click **Map** beside the zoom controls at the bottom right of the map. On mobile, first use the floating Map button to switch from the listing view to the map.

The panel reproduces the supplied reference's Map Options heading, three view choices, and two-column Climate Risk choices.

| Choice | Behaviour |
| --- | --- |
| Automatic | OpenStreetMap street basemap; default selection |
| Satellite | Esri World Imagery tiles; keeps the current centre, zoom, and property pins |
| Street view | Shows a link to Google Maps Street View at the current map centre; opens in a new tab |
| None selected | Default climate setting; clears any unavailable-data notice |
| Wind / Flood / Air / Fire / Heat | Selects the requested risk type and clearly reports that risk data is unavailable; no overlay is drawn |

Selections persist while navigating/filtering the current search. Outside clicks close the menu. Escape closes it and returns focus to its Map button. Native radio inputs support keyboard navigation. The menu scrolls in short viewports and stays within the map on tablets and phones.

Satellite imagery requires network access to the Esri tile service. Attribution is displayed on the map and changes with the chosen provider. If imagery cannot load, the map presents an option to return to Automatic. Street View availability depends on Google's coverage at the selected location; the portal does not embed Google panoramas or supply an API key.

An appropriate India climate-risk provider is required before real risk overlays can be enabled. The current UI does not infer a home's risk from its appearance or from fictional seed data.

References: [Esri basemap layers](https://developers.arcgis.com/esri-leaflet/maps/display-multiple-basemap-layers/), [Google Maps URL documentation](https://developers.google.com/maps/documentation/urls/get-started), [Esri attribution guidance](https://support.esri.com/en-us/knowledge-base/what-is-the-correct-way-to-cite-an-arcgis-online-basema-000012040).

## Draw a boundary

Draw opens Pen mode: hold, draw around an area and release. Filtered price pins remain visible in Pen, Move map and preview, with popup clicks disabled until drawing ends. Hovering a result card adds a thin cyan border and soft glow to its matching map pin. A compact 24px pen cursor marks the drawing point; Move map and finished-area refinement use a hand. Use Redraw or Edit area to adjust a boundary, then Apply. Results are filtered on the server; URLs and saved searches retain the polygon and original location. Remove Boundary restores the original city and retains price, room and other filters, even after a refresh. An original all-India search returns to all India. Older area links without return context use the all-India fallback. See [drawn-area search](DRAW-SEARCH.md).
