# Draw an area with a pen

Updated: 11 October 2026.

Open a property search and choose **Draw** on the map. On phones, switch to **Map** first. Pen is selected automatically. Properties matching your current filters remain visible throughout drawing, moving the map and adjusting the preview. Property pins do not open popups while drawing, so you can trace across them. Results change only when you choose Apply.

1. Press and hold the mouse button, or touch the map with your finger.
2. Draw around the area you want in one continuous stroke.
3. Release. RealSite closes and shades the area automatically.
4. Choose **Apply** to search inside it.

The compact pen cursor is 24x24 pixels with a thin blue outline and white edge. Its tip is the drawing point, including while holding the mouse button. A hand cursor indicates Move map or editing the finished area. Touch input uses your finger.

Hovering a result card highlights its matching visible map pin with a thin cyan border and soft glow; moving the pointer away clears the highlight. Sale and rental results share this behaviour.

The stroke follows your movement in real time. It uses a single line updated once per animation frame; individual corner markers appear only after release.

- **Redraw** starts a new stroke if you want to try again.
- **Move map** lets you pan or zoom before drawing. Select **Pen** to draw again.
- After release, drag the small white corner handles to refine the shape.
- **Edit area** adjusts an applied boundary without starting from scratch.
- **Cancel**, or Escape, keeps the previously applied search.
- **Remove Boundary** restores the location you searched before drawing (for example, Hyderabad). Other property filters remain active. A search started without a location returns to all India.
- Applying clears the text location and temporary viewport bounds. Price, bedrooms, property type and More Filters still apply.
- The polygon and original location stay in the URL and saved searches. Reload and browser navigation restore them. Editing or redrawing retains the original location; searching a new location clears the boundary.

Small accidental loops or overruns where the stroke joins are trimmed automatically before the preview appears. The largest traced region is retained, including concave edges. A substantial crossed shape (such as a figure eight) or a very small stroke shows guidance and cannot apply. Use Redraw or move the handles to fix it. One region with up to 64 corners is supported; the stroke is simplified after release to preserve its outline. Counts, pagination, map markers and price distribution share the server predicate. Edge points and concave polygons are supported.

Keyboard alternative: focus the map in Pen mode, use arrow keys to position its centre, Enter to add corners and Shift+Enter to finish. Escape cancels.

`polygon` contains the area and `boundary_q` remembers the original text location as return context, without restricting the area to that city. Older drawn links without return context return to all India. The PostgreSQL/SQLite predicate and JSON saved-search storage need no schema changes. See [testing](TESTING.md) and [handoff](HANDOFF.md).
