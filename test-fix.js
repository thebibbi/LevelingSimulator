// Test to verify the fix for the symmetry issue
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

function defaultGeometry() {
  const baseRadius = 120; // mm
  const platRadius = 70;  // mm
  const basePhase = 0 * DEG2RAD;
  const platPhase = 30 * DEG2RAD;  // Key fix: 30 degrees rotation
  const l0 = Array(6).fill(150); // nominal absolute lengths (mm)
  const basePts = regularHex(baseRadius, 0, basePhase);
  const platLocal = triPoints(platRadius, 0, platPhase);
  const legPairs = [ [0,1,0], [2,3,1], [4,5,2] ];
  const legToPidx = [0, 0, 1, 1, 2, 2];  // Original mapping
  return { basePts, platLocal, l0, legPairs, legToPidx };
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

// Run the specific test that was failing
function testPairSymmetry() {
  const geom = defaultGeometry();
  const ik = inverseKinematics(geom, [0,0,160, 0,0,0]);
  const L = ik.lengthsAbs;
  
  console.log('Leg lengths at neutral pose:', L);
  
  const pair1Diff = Math.abs(L[0]-L[1]);
  const pair2Diff = Math.abs(L[2]-L[3]);
  const pair3Diff = Math.abs(L[4]-L[5]);
  
  console.log('Pair 1 (0,1) difference:', pair1Diff);
  console.log('Pair 2 (2,3) difference:', pair2Diff);
  console.log('Pair 3 (4,5) difference:', pair3Diff);
  
  const tolerance = 1e-6;
  const pair1OK = pair1Diff < tolerance;
  const pair2OK = pair2Diff < tolerance;
  const pair3OK = pair3Diff < tolerance;
  
  console.log('Pair 1 symmetry OK:', pair1OK);
  console.log('Pair 2 symmetry OK:', pair2OK);
  console.log('Pair 3 symmetry OK:', pair3OK);
  
  const allOK = pair1OK && pair2OK && pair3OK;
  console.log('All pairs symmetric:', allOK);
  
  return allOK;
}

// Run the test
const result = testPairSymmetry();
console.log('\nTest result:', result ? 'PASSED' : 'FAILED');
process.exit(result ? 0 : 1);
