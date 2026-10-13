import assert from 'node:assert/strict';
import { tidyStroke } from '../src/stroke-shape.js';
const area=p=>Math.abs(p.reduce((s,a,i)=>{const b=p[(i+1)%p.length];return s+a[0]*b[1]-a[1]*b[0];},0))/2;
const box=[[0,0],[300,0],[300,240],[0,240]];
assert.deepEqual(tidyStroke(box),box);
assert.deepEqual(tidyStroke([...box,box[0]]),box);
assert.deepEqual(tidyStroke([[0,0],[0,0],...box.slice(1)]),box);
// Returning to the start then overrunning the first edge used to be invalid.
const overrun=[...box,[0,0],[25,0],[25,12]];
const fixed=tidyStroke(overrun);
assert.ok(fixed.length>=3);assert.ok(area(fixed)>=area(box)*.98);
assert.equal(area(tidyStroke(overrun.toReversed())),area(fixed));
// Concavity must survive cleanup; the missing notch is not filled in.
const concave=[[0,0],[300,0],[300,100],[120,100],[120,240],[0,240]];
const concaveFixed=tidyStroke([...concave,[0,0],[20,0],[20,8]]);
assert.equal(area(concaveFixed),area(concave));
assert.ok(area(concaveFixed)<300*240);
// A tiny loop at the joining edge is trimmed, not rejected.
const join=[[0,8],[15,12],[0,0],[300,0],[300,240],[0,240]];
assert.ok(area(tidyStroke(join))>=area(box)*.99);
// Large crossed regions retain their geometry for the existing error/repair UI.
const eight=[[0,0],[300,240],[0,240],[300,0]];
assert.deepEqual(tidyStroke(eight),eight);
assert.deepEqual(tidyStroke([[0,0],[1,1],[0,1],[1,0]]),[[0,0],[1,1],[0,1],[1,0]]);
console.log('Stroke cleanup checks passed: exact closure, overruns, winding, concavity and genuine crossings.');
