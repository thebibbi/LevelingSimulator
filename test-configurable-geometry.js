// Test script to verify configurable geometry works correctly
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

function getGeometry(configType = '6-3', params = {}) {
  // Default parameters
  const {
    baseRadius: baseRadiusParam = 120,
    platRadius: platRadiusParam = 70,
    l0: l0Param = 150
  } = params;
  
  switch(configType) {
    case '8-8':
      // 8-8 configuration: 8 base points, 8 platform points
      const baseRadius88 = baseRadiusParam; // mm
      const platRadius88 = platRadiusParam;  // mm
      const basePhase88 = 0 * DEG2RAD;
      const platPhase88 = 0 * DEG2RAD;
      const l0_88 = Array(8).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius66 = baseRadiusParam; // mm
      const platRadius66 = platRadiusParam;  // mm
      const basePhase66 = 0 * DEG2RAD;
      const platPhase66 = 0 * DEG2RAD;
      const l0_66 = Array(6).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius63r = baseRadiusParam; // mm
      const platRadius63r = platRadiusParam;  // mm
      const basePhase63r = 0 * DEG2RAD;
      const platPhase63r = 30 * DEG2RAD;
      // 6 legs for redundancy (same as standard 6-3 but with different mapping)
      const l0_63r = Array(6).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius63a = baseRadiusParam; // mm
      const platRadius63a = platRadiusParam;  // mm
      const basePhase63a = 0 * DEG2RAD;
      const platPhase63a = 0 * DEG2RAD; // No phase shift for asymmetric arrangement
      const l0_63a = Array(6).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius44 = baseRadiusParam; // mm
      const platRadius44 = platRadiusParam;  // mm
      const basePhase44 = 0 * DEG2RAD;
      const platPhase44 = 0 * DEG2RAD;
      const l0_44 = Array(4).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius33 = baseRadiusParam; // mm
      const platRadius33 = platRadiusParam;  // mm
      const basePhase33 = 0 * DEG2RAD;
      const platPhase33 = 30 * DEG2RAD;
      const l0_33 = Array(3).fill(l0Param); // nominal absolute lengths (mm)
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
      const baseRadius = baseRadiusParam; // mm
      const platRadius = platRadiusParam;  // mm
      const basePhase = 0 * DEG2RAD;
      const platPhase = 30 * DEG2RAD;
      const l0 = Array(6).fill(l0Param); // nominal absolute lengths (mm)
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

// Test configurable geometry
console.log('Testing Configurable Geometry');
console.log('===============================');

// Test with default parameters
console.log('\n--- Testing with default parameters ---');
const geomDefault = getGeometry('6-3');
console.log('Base radius:', Math.hypot(geomDefault.basePts[0][0], geomDefault.basePts[0][1]));
console.log('Platform radius:', Math.hypot(geomDefault.platLocal[0][0], geomDefault.platLocal[0][1]));
console.log('Nominal leg length:', geomDefault.l0[0]);

// Test with custom parameters
console.log('\n--- Testing with custom parameters ---');
const customParams = {
  baseRadius: 150,
  platRadius: 80,
  l0: 200
};
const geomCustom = getGeometry('6-3', customParams);
console.log('Base radius:', Math.hypot(geomCustom.basePts[0][0], geomCustom.basePts[0][1]));
console.log('Platform radius:', Math.hypot(geomCustom.platLocal[0][0], geomCustom.platLocal[0][1]));
console.log('Nominal leg length:', geomCustom.l0[0]);

// Test inverse kinematics with custom parameters
console.log('\n--- Testing inverse kinematics with custom parameters ---');
const ikCustom = inverseKinematics(geomCustom, [0,0,200, 0,0,0]);
console.log('Leg lengths at neutral pose:', ikCustom.lengthsAbs.map(l => l.toFixed(2)));

// Test different configurations with custom parameters
console.log('\n--- Testing different configurations with custom parameters ---');
const configs = ['8-8', '6-6', '6-3-redundant', '6-3-asymmetric', '4-4', '3-3'];
configs.forEach(config => {
  const geom = getGeometry(config, customParams);
  console.log(`${config}: Base points=${geom.basePts.length}, Platform points=${geom.platLocal.length}, Legs=${geom.l0.length}`);
});

console.log('\nConfigurable geometry test completed successfully!');
