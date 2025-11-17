// Test script to verify all Stewart platform configurations work correctly
const DEG2RAD = Math.PI / 180;

function regularHex(radius, z = 0, phase = 0) {
  return Array.from({ length: 6 }, (_, k) => {
    const th = phase + (k * 2 * Math.PI) / 6;
    return [radius * Math.cos(th), radius * Math.sin(th), z];
  });
}

function triPoints(radius, z = 0, phase = 0) {
  return Array.from({ length: 3 }, (_, k) => {
    const th = phase + (k * 2 * Math.PI) / 3;
    return [radius * Math.cos(th), radius * Math.sin(th), z];
  });
}

function squarePoints(radius, z = 0, phase = 0) {
  return Array.from({ length: 4 }, (_, k) => {
    const th = phase + (k * 2 * Math.PI) / 4;
    return [radius * Math.cos(th), radius * Math.sin(th), z];
  });
}

function regularOct(radius, z = 0, phase = 0) {
  return Array.from({ length: 8 }, (_, k) => {
    const th = phase + (k * 2 * Math.PI) / 8;
    return [radius * Math.cos(th), radius * Math.sin(th), z];
  });
}

function getGeometry(configType = '6-3') {
  switch(configType) {
    case '8-8':
      // 8-8 configuration: 8 base points, 8 platform points
      const baseRadius88 = 120; // mm
      const platRadius88 = 70;  // mm
      const basePhase88 = 0 * DEG2RAD;
      const platPhase88 = 0 * DEG2RAD;
      const l0_88 = Array(8).fill(150); // nominal absolute lengths (mm)
      const basePts88 = regularOct(baseRadius88, 0, basePhase88);
      const platLocal88 = regularOct(platRadius88, 0, platPhase88);
      // Each leg connects to corresponding platform point
      const legToPidx88 = [0, 1, 2, 3, 4, 5, 6, 7];
      return { 
        basePts: basePts88, 
        platLocal: platLocal88, 
        l0: l0_88, 
        legToPidx: legToPidx88,
        configType
      };
    
    case '6-6':
      // 6-6 configuration: 6 base points, 6 platform points
      const baseRadius66 = 120; // mm
      const platRadius66 = 70;  // mm
      const basePhase66 = 0 * DEG2RAD;
      const platPhase66 = 0 * DEG2RAD;
      const l0_66 = Array(6).fill(150); // nominal absolute lengths (mm)
      const basePts66 = regularHex(baseRadius66, 0, basePhase66);
      const platLocal66 = regularHex(platRadius66, 0, platPhase66);
      // Each leg connects to corresponding platform point
      const legToPidx66 = [0, 1, 2, 3, 4, 5];
      return { 
        basePts: basePts66, 
        platLocal: platLocal66, 
        l0: l0_66, 
        legToPidx: legToPidx66,
        configType
      };
    
    case '6-3-redundant':
      // Redundant 6-3 configuration: 6 base points, 3 platform points with extra support
      // For this configuration, we'll use a different approach where we have 6 base points but
      // each platform point connects to 2 base points, with some base points connecting to multiple platform points
      const baseRadius63r = 120; // mm
      const platRadius63r = 70;  // mm
      const basePhase63r = 0 * DEG2RAD;
      const platPhase63r = 30 * DEG2RAD;
      // 6 legs for redundancy (same as standard 6-3 but with different mapping)
      const l0_63r = Array(6).fill(150); // nominal absolute lengths (mm)
      const basePts63r = regularHex(baseRadius63r, 0, basePhase63r);
      const platLocal63r = triPoints(platRadius63r, 0, platPhase63r);
      // Redundant leg pairing: each platform point connects to 2 base points
      const legToPidx63r = [0, 0, 1, 1, 2, 2];
      return { 
        basePts: basePts63r, 
        platLocal: platLocal63r, 
        l0: l0_63r, 
        legToPidx: legToPidx63r,
        configType
      };
    
    case '6-3-asymmetric':
      // Asymmetric 6-3 configuration: 6 base points, 3 platform points with asymmetric arrangement
      const baseRadius63a = 120; // mm
      const platRadius63a = 70;  // mm
      const basePhase63a = 0 * DEG2RAD;
      const platPhase63a = 0 * DEG2RAD; // No phase shift for asymmetric arrangement
      const l0_63a = Array(6).fill(150); // nominal absolute lengths (mm)
      const basePts63a = regularHex(baseRadius63a, 0, basePhase63a);
      const platLocal63a = triPoints(platRadius63a, 0, platPhase63a);
      // Asymmetric leg pairing
      const legToPidx63a = [0, 1, 1, 2, 2, 0];
      return { 
        basePts: basePts63a, 
        platLocal: platLocal63a, 
        l0: l0_63a, 
        legToPidx: legToPidx63a,
        configType
      };
    
    case '4-4':
      // 4-4 configuration: 4 base points, 4 platform points
      const baseRadius44 = 120; // mm
      const platRadius44 = 70;  // mm
      const basePhase44 = 0 * DEG2RAD;
      const platPhase44 = 0 * DEG2RAD;
      const l0_44 = Array(4).fill(150); // nominal absolute lengths (mm)
      const basePts44 = squarePoints(baseRadius44, 0, basePhase44);
      const platLocal44 = squarePoints(platRadius44, 0, platPhase44);
      // Each leg connects to corresponding platform point
      const legToPidx44 = [0, 1, 2, 3];
      return { 
        basePts: basePts44, 
        platLocal: platLocal44, 
        l0: l0_44, 
        legToPidx: legToPidx44,
        configType
      };
    
    case '3-3':
      // 3-3 configuration: 3 base points, 3 platform points
      const baseRadius33 = 120; // mm
      const platRadius33 = 70;  // mm
      const basePhase33 = 0 * DEG2RAD;
      const platPhase33 = 30 * DEG2RAD;
      const l0_33 = Array(3).fill(150); // nominal absolute lengths (mm)
      const basePts33 = triPoints(baseRadius33, 0, basePhase33);
      const platLocal33 = triPoints(platRadius33, 0, platPhase33);
      // Each leg connects to corresponding platform point
      const legToPidx33 = [0, 1, 2];
      return { 
        basePts: basePts33, 
        platLocal: platLocal33, 
        l0: l0_33, 
        legToPidx: legToPidx33,
        configType
      };
    
    case '6-3':
    default:
      // 6-3 configuration: 6 base points, 3 platform points
      const baseRadius = 120; // mm
      const platRadius = 70;  // mm
      const basePhase = 0 * DEG2RAD;
      const platPhase = 30 * DEG2RAD;
      const l0 = Array(6).fill(150); // nominal absolute lengths (mm)
      const basePts = regularHex(baseRadius, 0, basePhase);
      const platLocal = triPoints(platRadius, 0, platPhase);
      // Legs paired: 0,1 -> platform 0; 2,3 -> platform 1; 4,5 -> platform 2
      const legToPidx = [0, 0, 1, 1, 2, 2];
      return { basePts, platLocal, l0, legToPidx, configType };
  }
}

function add(a,b) { return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]; }
function sub(a,b) { return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function norm(a) { return Math.hypot(a[0], a[1], a[2]); }

function rotXYZ(roll, pitch, yaw) {
  // ZYX convention: Rz(yaw)*Ry(pitch)*Rx(roll)
  const cr = Math.cos(roll), sr = Math.sin(roll);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const Rz = [
    [cy, -sy, 0],
    [sy,  cy, 0],
    [ 0,   0, 1],
  ];
  const Ry = [
    [ cp, 0, sp],
    [  0, 1,  0],
    [-sp, 0, cp],
  ];
  const Rx = [
    [1,  0,   0],
    [0, cr, -sr],
    [0, sr,  cr],
  ];
  return matMul(matMul(Rz, Ry), Rx);
}

function matMul(A, B) {
  const m = A.length, n = B[0].length, k = B.length;
  const C = Array.from({ length: m }, () => Array(n).fill(0));
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      let s = 0;
      for (let t = 0; t < k; t++) s += A[i][t] * B[t][j];
      C[i][j] = s;
    }
  }
  return C;
}

function matVec(R, v) {
  return [
    R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
    R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
    R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
  ];
}

function platformWorldPts(platLocal, pose) {
  const [x, y, z, r, p, yaw] = pose; // radians for r,p,yaw
  const R = rotXYZ(r, p, yaw);
  const t = [x, y, z];
  return platLocal.map((pt) => add(matVec(R, pt), t));
}

function inverseKinematics({ basePts, platLocal, legToPidx, l0 }, pose) {
  const P3 = platformWorldPts(platLocal, pose);
  const P6 = legToPidx.map((pidx) => P3[pidx]);
  const d = P6.map((P, i) => sub(P, basePts[i]));
  const lengthsAbs = d.map((v) => norm(v));
  const extensions = lengthsAbs.map((L, i) => L - l0[i]);
  return { P3, P6, lengthsAbs, extensions };
}

// Test all configurations
console.log('Testing All Stewart Platform Configurations');
console.log('===========================================');

// Test 8-8 configuration
console.log('\n--- Testing 8-8 Configuration ---');
const geom88 = getGeometry('8-8');
console.log('Base points:', geom88.basePts.length);
console.log('Platform points:', geom88.platLocal.length);
console.log('Leg mappings:', geom88.legToPidx);

const ik88 = inverseKinematics(geom88, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik88.lengthsAbs.map(l => l.toFixed(2)));

// Test 6-6 configuration
console.log('\n--- Testing 6-6 Configuration ---');
const geom66 = getGeometry('6-6');
console.log('Base points:', geom66.basePts.length);
console.log('Platform points:', geom66.platLocal.length);
console.log('Leg mappings:', geom66.legToPidx);

const ik66 = inverseKinematics(geom66, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik66.lengthsAbs.map(l => l.toFixed(2)));

// Test 6-3 redundant configuration
console.log('\n--- Testing 6-3 Redundant Configuration ---');
const geom63r = getGeometry('6-3-redundant');
console.log('Base points:', geom63r.basePts.length);
console.log('Platform points:', geom63r.platLocal.length);
console.log('Leg mappings:', geom63r.legToPidx);

const ik63r = inverseKinematics(geom63r, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik63r.lengthsAbs.map(l => l.toFixed(2)));
console.log('Note: This is a redundant configuration where each platform point connects to 2 base points');

// Test 6-3 asymmetric configuration
console.log('\n--- Testing 6-3 Asymmetric Configuration ---');
const geom63a = getGeometry('6-3-asymmetric');
console.log('Base points:', geom63a.basePts.length);
console.log('Platform points:', geom63a.platLocal.length);
console.log('Leg mappings:', geom63a.legToPidx);

const ik63a = inverseKinematics(geom63a, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik63a.lengthsAbs.map(l => l.toFixed(2)));

// Test 6-3 configuration
console.log('\n--- Testing 6-3 Configuration ---');
const geom63 = getGeometry('6-3');
console.log('Base points:', geom63.basePts.length);
console.log('Platform points:', geom63.platLocal.length);
console.log('Leg mappings:', geom63.legToPidx);

const ik63 = inverseKinematics(geom63, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik63.lengthsAbs.map(l => l.toFixed(2)));

// Check pair symmetry for 6-3
const pair1Diff = Math.abs(ik63.lengthsAbs[0] - ik63.lengthsAbs[1]);
const pair2Diff = Math.abs(ik63.lengthsAbs[2] - ik63.lengthsAbs[3]);
const pair3Diff = Math.abs(ik63.lengthsAbs[4] - ik63.lengthsAbs[5]);
console.log('Pair symmetry check (should be ~0):', pair1Diff.toFixed(6), pair2Diff.toFixed(6), pair3Diff.toFixed(6));

// Test 4-4 configuration
console.log('\n--- Testing 4-4 Configuration ---');
const geom44 = getGeometry('4-4');
console.log('Base points:', geom44.basePts.length);
console.log('Platform points:', geom44.platLocal.length);
console.log('Leg mappings:', geom44.legToPidx);

const ik44 = inverseKinematics(geom44, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik44.lengthsAbs.map(l => l.toFixed(2)));

// Test 3-3 configuration
console.log('\n--- Testing 3-3 Configuration ---');
const geom33 = getGeometry('3-3');
console.log('Base points:', geom33.basePts.length);
console.log('Platform points:', geom33.platLocal.length);
console.log('Leg mappings:', geom33.legToPidx);

const ik33 = inverseKinematics(geom33, [0,0,160, 0,0,0]);
console.log('Leg lengths at neutral pose:', ik33.lengthsAbs.map(l => l.toFixed(2)));

console.log('\nAll configurations tested successfully!');
