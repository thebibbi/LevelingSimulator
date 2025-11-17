// Test script to verify validation functions work correctly

// Helper functions
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
  return [
    [
      Rz[0][0]*Ry[0][0]*Rx[0][0] + Rz[0][1]*Ry[1][0]*Rx[0][0] + Rz[0][2]*Ry[2][0]*Rx[0][0],
      Rz[0][0]*Ry[0][0]*Rx[0][1] + Rz[0][1]*Ry[1][0]*Rx[0][1] + Rz[0][2]*Ry[2][0]*Rx[0][1],
      Rz[0][0]*Ry[0][0]*Rx[0][2] + Rz[0][1]*Ry[1][0]*Rx[0][2] + Rz[0][2]*Ry[2][0]*Rx[0][2]
    ],
    [
      Rz[1][0]*Ry[0][0]*Rx[1][0] + Rz[1][1]*Ry[1][0]*Rx[1][0] + Rz[1][2]*Ry[2][0]*Rx[1][0],
      Rz[1][0]*Ry[0][0]*Rx[1][1] + Rz[1][1]*Ry[1][0]*Rx[1][1] + Rz[1][2]*Ry[2][0]*Rx[1][1],
      Rz[1][0]*Ry[0][0]*Rx[1][2] + Rz[1][1]*Ry[1][0]*Rx[1][2] + Rz[1][2]*Ry[2][0]*Rx[1][2]
    ],
    [
      Rz[2][0]*Ry[0][0]*Rx[2][0] + Rz[2][1]*Ry[1][0]*Rx[2][0] + Rz[2][2]*Ry[2][0]*Rx[2][0],
      Rz[2][0]*Ry[0][0]*Rx[2][1] + Rz[2][1]*Ry[1][0]*Rx[2][1] + Rz[2][2]*Ry[2][0]*Rx[2][1],
      Rz[2][0]*Ry[0][0]*Rx[2][2] + Rz[2][1]*Ry[1][0]*Rx[2][2] + Rz[2][2]*Ry[2][0]*Rx[2][2]
    ]
  ];
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

// Validation functions
function validatePlatformJointSpacing(platPts, minSpacing = 20) {
  // Check spacing between all pairs of platform points
  for (let i = 0; i < platPts.length; i++) {
    for (let j = i + 1; j < platPts.length; j++) {
      const dx = platPts[i][0] - platPts[j][0];
      const dy = platPts[i][1] - platPts[j][1];
      const dz = platPts[i][2] - platPts[j][2];
      const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
      
      if (distance < minSpacing) {
        return {
          valid: false,
          message: `Platform joints ${i} and ${j} are too close (${distance.toFixed(1)} mm < ${minSpacing} mm)`
        };
      }
    }
  }
  
  return { valid: true, message: "Platform joint spacing is valid" };
}

function validateBaseJointSpacing(basePts, minSpacing = 20) {
  // Check spacing between all pairs of base points
  for (let i = 0; i < basePts.length; i++) {
    for (let j = i + 1; j < basePts.length; j++) {
      const dx = basePts[i][0] - basePts[j][0];
      const dy = basePts[i][1] - basePts[j][1];
      const distance = Math.sqrt(dx*dx + dy*dy); // Only XY plane for base
      
      if (distance < minSpacing) {
        return {
          valid: false,
          message: `Base joints ${i} and ${j} are too close (${distance.toFixed(1)} mm < ${minSpacing} mm)`
        };
      }
    }
  }
  
  return { valid: true, message: "Base joint spacing is valid" };
}

function validateLegLengths(ikResult, l0, limits) {
  const { lengthsAbs } = ikResult;
  
  for (let i = 0; i < lengthsAbs.length; i++) {
    const length = lengthsAbs[i];
    
    // Check if leg is too short (compressed beyond limits)
    if (length < limits.lminAbs) {
      return {
        valid: false,
        message: `Leg ${i} is too short (${length.toFixed(1)} mm < ${limits.lminAbs} mm)`
      };
    }
    
    // Check if leg is too long (extended beyond limits)
    if (length > limits.lmaxAbs) {
      return {
        valid: false,
        message: `Leg ${i} is too long (${length.toFixed(1)} mm > ${limits.lmaxAbs} mm)`
      };
    }
    
    // Check if leg is extremely short (nearly collapsed)
    if (length < l0 * 0.5) {
      return {
        valid: false,
        message: `Leg ${i} is dangerously short (${length.toFixed(1)} mm < ${l0 * 0.5} mm)`
      };
    }
    
    // Check if leg is extremely long (over-extended)
    if (length > l0 * 1.8) {
      return {
        valid: false,
        message: `Leg ${i} is over-extended (${length.toFixed(1)} mm > ${l0 * 1.8} mm)`
      };
    }
  }
  
  return { valid: true, message: "Leg lengths are within safe limits" };
}

// Test validation functions
console.log('Testing Validation Functions');
console.log('============================');

// Test platform joint spacing validation
console.log('\n--- Testing Platform Joint Spacing Validation ---');
const platformPoints = [
  [0, 0, 160],
  [50, 0, 160],
  [25, 43.3, 160]  // Points that are far apart
];
const platformValidation = validatePlatformJointSpacing(platformPoints);
console.log('Valid platform spacing:', platformValidation);

// Test with points that are too close
const closePlatformPoints = [
  [0, 0, 160],
  [5, 0, 160],
  [2.5, 4.3, 160]  // Points that are too close
];
const closePlatformValidation = validatePlatformJointSpacing(closePlatformPoints);
console.log('Invalid platform spacing:', closePlatformValidation);

// Test base joint spacing validation
console.log('\n--- Testing Base Joint Spacing Validation ---');
const basePoints = [
  [120, 0, 0],
  [60, 103.9, 0],
  [-60, 103.9, 0],
  [-120, 0, 0],
  [-60, -103.9, 0],
  [60, -103.9, 0]  // Points that are far apart
];
const baseValidation = validateBaseJointSpacing(basePoints);
console.log('Valid base spacing:', baseValidation);

// Test with points that are too close
const closeBasePoints = [
  [120, 0, 0],
  [125, 0, 0],
  [122.5, 2, 0]  // Points that are too close
];
const closeBaseValidation = validateBaseJointSpacing(closeBasePoints);
console.log('Invalid base spacing:', closeBaseValidation);

// Test leg length validation
console.log('\n--- Testing Leg Length Validation ---');
const ikResult = {
  lengthsAbs: [150, 160, 170, 180, 190, 200]
};
const l0 = 150;
const limits = { lminAbs: 140, lmaxAbs: 220 };
const legValidation = validateLegLengths(ikResult, l0, limits);
console.log('Valid leg lengths:', legValidation);

// Test with invalid leg lengths
const invalidIkResult = {
  lengthsAbs: [130, 160, 170, 180, 190, 230]  // Some outside limits
};
const invalidLegValidation = validateLegLengths(invalidIkResult, l0, limits);
console.log('Invalid leg lengths:', invalidLegValidation);

console.log('\nValidation tests completed successfully!');
