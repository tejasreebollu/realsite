// Trim tiny closing loops without replacing a user's outline with a convex hull.
// Screen coordinates [x, y] keep the tolerance independent of the map zoom.
const cross = (a,b) => a[0]*b[1]-a[1]*b[0];
const subtract = (a,b) => [a[0]-b[0],a[1]-b[1]];
const distance = (a,b) => Math.hypot(a[0]-b[0],a[1]-b[1]);
const area = points => Math.abs(points.reduce((sum,a,i) => sum+cross(a,points[(i+1)%points.length]),0))/2;
function uniqueNeighbours(points) {
  const result = points.filter((p,i) => !i || distance(p,points[i-1])>.05);
  if(result.length>1 && distance(result[0],result.at(-1))<=.05) result.pop();
  return result;
}
function intersection(a,b,c,d) {
  const ab=subtract(b,a), cd=subtract(d,c), ac=subtract(c,a), denominator=cross(ab,cd);
  if(Math.abs(denominator)<1e-8) return null;
  const t=cross(ac,cd)/denominator, u=cross(ac,ab)/denominator;
  if(t < -1e-8 || t > 1+1e-8 || u < -1e-8 || u > 1+1e-8) return null;
  return [a[0]+Math.max(0,Math.min(1,t))*ab[0],a[1]+Math.max(0,Math.min(1,t))*ab[1]];
}
export function tidyStroke(input) {
  let points=uniqueNeighbours(input), discarded=0;
  for(let pass=0;pass<12;pass++) {
    let replacement=null;
    for(let i=0;i<points.length && !replacement;i++) for(let j=i+2;j<points.length;j++) {
      if(i===0 && j===points.length-1) continue;
      const hit=intersection(points[i],points[(i+1)%points.length],points[j],points[(j+1)%points.length]);
      if(!hit) continue;
      const a=uniqueNeighbours([hit,...points.slice(i+1,j+1)]);
      const b=uniqueNeighbours([hit,...points.slice(j+1),...points.slice(0,i+1)]);
      const aa=area(a), bb=area(b), larger=aa>=bb ? a : b;
      const keep=Math.max(aa,bb), trim=Math.min(aa,bb);
      // Only small accidental loops are removed. A substantial second region
      // (such as a figure eight) stays invalid instead of silently losing an area.
      if(larger.length>=3 && keep>=64 && discarded+trim<=keep*.08) {
        replacement=larger;discarded+=trim;break;
      }
    }
    if(!replacement) break;
    points=replacement;
  }
  return points;
}
