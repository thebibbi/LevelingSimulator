import React, { useMemo, useState, useRef, useEffect, useCallback } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Line, Sphere } from "@react-three/drei";

/**
 * Stewart 6-3 Browser Visualizer (robust R3F-safe build)
 *
 * WHAT WAS FIXED
 * - All React-Three-Fiber hooks (useFrame) are strictly inside <Canvas>.
 * - Animation runs in <StewartStage/> (inside Canvas). Parent UI is pure React.
 * - Added strong prop/shape guards and stable refs to prevent undefined access during frames.
 * - Converted all Line points to THREE.Vector3[] to avoid adapter edge-cases.
 * - Throttled parent pose syncing and guarded against undefined callbacks.
 *
 * WHY: You hit a runtime "TypeError: can't access property 'source', e83 is undefined".
 * In practice this often stems from a stale/undefined prop crossing roots during a frame update
 * (e.g., Canvas child calls a parent setter which triggers a re-render mid-frame), or from passing
 * non-stable/invalid props to Drei primitives. The changes above harden those paths.
 */

// ------------------ Math helpers ------------------ //
const DEG2RAD = Math.PI / 180;

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

const add = (a,b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]];
const sub = (a,b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
const norm = (a) => Math.hypot(a[0], a[1], a[2]);

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

// ------------------ Core IK for 6-3 ------------------ //
function defaultGeometry() {
  const baseRadius = 120; // mm
  const platRadius = 70;  // mm
  const basePhase = 0 * DEG2RAD;
  const platPhase = 0 * DEG2RAD;
  const l0 = Array(6).fill(150); // nominal absolute lengths (mm)
  const basePts = regularHex(baseRadius, 0, basePhase);
  const platLocal = triPoints(platRadius, 0, platPhase);
  const legPairs = [ [0,1,0], [2,3,1], [4,5,2] ];
  const legToPidx = [0,0,1,1,2,2];
  return { basePts, platLocal, l0, legPairs, legToPidx };
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

// ------------------ Utils for Drei Line ------------------ //
function toVec3(pointsArr) {
  // Accepts [[x,y,z], ...] and returns THREE.Vector3[]
  return pointsArr.map((p) => new THREE.Vector3(p[0], p[1], p[2]));
}

// ------------------ R3F stage (inside Canvas only) ------------------ //
function StewartStage({ pose, anim, geom, onPose }) {
  // Local animated pose lives INSIDE Canvas (safe for useFrame)
  const [localPose, setLocalPose] = useState(() => pose || { x:0, y:0, z:160, roll:0, pitch:0, yaw:0 });

  // Stable callback ref to avoid capturing stale parent setter during frames
  const onPoseRef = useRef(onPose);
  useEffect(() => { onPoseRef.current = onPose; }, [onPose]);

  const throttler = useRef({ last: 0 });

  useFrame((state) => {
    if (!anim) return;
    const t = state.clock.elapsedTime;
    const x = 10 * Math.sin(2*Math.PI*0.5*t);
    const y = 10 * Math.sin(2*Math.PI*0.25*t + Math.PI/3);
    const z = 160 + 5 * Math.sin(2*Math.PI*0.2*t);
    const roll = 2 * Math.sin(2*Math.PI*0.2*t);
    const pitch = 2 * Math.sin(2*Math.PI*0.27*t + 0.6);
    const yaw = 5 * Math.sin(2*Math.PI*0.15*t);

    const p = { x, y, z, roll, pitch, yaw };
    setLocalPose(p);

    // Throttle syncing to parent UI (~15 Hz) and guard against undefined callback
    if (onPoseRef.current && typeof onPoseRef.current === "function") {
      if (t - throttler.current.last > 1/15) {
        try { onPoseRef.current(p); } catch { /* no-op */ }
        throttler.current.last = t;
      }
    }
  });

  // Choose which pose to render: animated or UI-driven
  const usedPose = anim ? localPose : (pose || { x:0, y:0, z:160, roll:0, pitch:0, yaw:0 });
  const pRad = [
    usedPose.x, usedPose.y, usedPose.z,
    usedPose.roll*DEG2RAD, usedPose.pitch*DEG2RAD, usedPose.yaw*DEG2RAD
  ];

  // Defensive geometry guards
  const { basePts, platLocal, legToPidx, l0 } = geom || {};
  const validGeom = Array.isArray(basePts) && basePts.length===6 && Array.isArray(platLocal) && platLocal.length===3 && Array.isArray(legToPidx) && legToPidx.length===6 && Array.isArray(l0) && l0.length===6;
  if (!validGeom) return null;

  const { P3, P6 } = useMemo(() => inverseKinematics({ basePts, platLocal, legToPidx, l0 }, pRad), [basePts, platLocal, legToPidx, l0, usedPose]);

  // Close the platform triangle for drawing
  const tri = useMemo(() => toVec3([...P3, P3[0]]), [P3]);

  // Ground ring for reference
  const baseRing = useMemo(() => {
    const n = 64; const r = Math.hypot(basePts[0][0], basePts[0][1]);
    const arr = Array.from({ length: n+1 }, (_, i) => {
      const th = (i / n) * 2 * Math.PI;
      return [r * Math.cos(th), r * Math.sin(th), 0];
    });
    return toVec3(arr);
  }, [basePts]);

  return (
    <>
      {/* Helpers */}
      <gridHelper args={[400, 20]} />
      <axesHelper args={[80]} />

      {/* Base ring & anchors */}
      <Line points={baseRing} />
      {basePts.map((B, i) => (
        <Sphere key={"b"+i} args={[2, 16, 16]} position={new THREE.Vector3(B[0], B[1], B[2])}>
          <meshStandardMaterial />
        </Sphere>
      ))}

      {/* Platform triangle & joints */}
      <Line points={tri} />
      {P3.map((P, i) => (
        <Sphere key={"p"+i} args={[2.5, 16, 16]} position={new THREE.Vector3(P[0], P[1], P[2])}>
          <meshStandardMaterial />
        </Sphere>
      ))}

      {/* Legs */}
      {basePts.map((B, i) => (
        <Line key={i} points={toVec3([[B[0],B[1],B[2]], P6[i]])} />
      ))}

      <ambientLight intensity={0.7} />
      <directionalLight intensity={0.7} position={[200, 200, 300]} />
      <OrbitControls makeDefault enableDamping />
    </>
  );
}

// ------------------ Self-tests (kept + more) ------------------ //
function runSelfTests() {
  const details = [];
  let passed = 0, failed = 0;
  const pass = (msg) => { details.push(`✅ ${msg}`); passed++; };
  const fail = (msg) => { details.push(`❌ ${msg}`); failed++; };
  const eps = 1e-6;

  // Test 1: Rotation orthogonality
  {
    const R = rotXYZ(0.3, -0.2, 0.7);
    const Rt = [[R[0][0], R[1][0], R[2][0]],[R[0][1], R[1][1], R[2][1]],[R[0][2], R[1][2], R[2][2]]];
    const I = matMul(Rt, R);
    const ok = Math.abs(I[0][0]-1)<1e-6 && Math.abs(I[1][1]-1)<1e-6 && Math.abs(I[2][2]-1)<1e-6;
    ok ? pass("rotXYZ returns orthonormal matrix (diag≈1)") : fail("rotXYZ orthogonality failed");
  }

  // Test 2: Platform XY radius preserved under yaw rotation
  {
    const geom = defaultGeometry();
    const yaw = 0.9;
    const P3 = platformWorldPts(geom.platLocal, [0,0,0, 0,0, yaw]);
    const rads = P3.map(p => Math.hypot(p[0], p[1]));
    const ok = rads.every(r => Math.abs(r - 70) < 1e-6);
    ok ? pass("Yaw rotation preserves platform radial distance") : fail("Yaw rotation broke platform radius");
  }

  // Test 3: Z translation sets P3.z ≈ z when roll/pitch=0
  {
    const geom = defaultGeometry();
    const z = 160;
    const P3 = platformWorldPts(geom.platLocal, [0,0,z, 0,0, 0]);
    const ok = P3.every(p => Math.abs(p[2] - z) < eps);
    ok ? pass("Z translation applied to platform joints") : fail("Z translation not applied correctly");
  }

  // Test 4: Pair symmetry at neutral pose (legs of each pair equal)
  {
    const geom = defaultGeometry();
    const ik = inverseKinematics(geom, [0,0,160, 0,0,0]);
    const L = ik.lengthsAbs;
    const ok = Math.abs(L[0]-L[1])<1e-6 && Math.abs(L[2]-L[3])<1e-6 && Math.abs(L[4]-L[5])<1e-6;
    ok ? pass("Neutral pose: paired legs have equal lengths") : fail("Pair symmetry failed at neutral pose");
  }

  // Test 5: Lengths are positive at nominal neutral pose
  {
    const geom = defaultGeometry();
    const ik = inverseKinematics(geom, [0,0,160, 0,0,0]);
    const ok = ik.lengthsAbs.every(v => v > 0);
    ok ? pass("Neutral pose: all absolute lengths positive") : fail("Found non-positive absolute length");
  }

  // Test 6 (NEW): IK returns arrays of correct sizes
  {
    const geom = defaultGeometry();
    const ik = inverseKinematics(geom, [0,0,160, 0,0,0]);
    const ok = Array.isArray(ik.P3) && ik.P3.length===3 && Array.isArray(ik.P6) && ik.P6.length===6 && Array.isArray(ik.lengthsAbs) && ik.lengthsAbs.length===6;
    ok ? pass("IK shapes: P3[3], P6[6], lengths[6]") : fail("IK shapes incorrect");
  }

  const summary = { passed, failed, details };
  /* eslint-disable no-console */
  console.group("Stewart 6-3 Self-Tests");
  details.forEach(d => console.log(d));
  console.log(`Summary: ${passed} passed, ${failed} failed`);
  console.groupEnd();
  /* eslint-enable no-console */
  return summary;
}

// ------------------ Main UI ------------------ //
export default function App() {
  const geom = useMemo(() => defaultGeometry(), []);
  const [pose, setPose] = useState(() => ({ x: 0, y: 0, z: 160, roll: 0, pitch: 0, yaw: 0 }));
  const [limits, setLimits] = useState({ lminAbs: 140, lmaxAbs: 220 });
  const [anim, setAnim] = useState(false);
  const tests = useMemo(() => runSelfTests(), []);

  const sliders = [
    { key: "x", min: -50, max: 50, step: 0.5, label: "X (mm)" },
    { key: "y", min: -50, max: 50, step: 0.5, label: "Y (mm)" },
    { key: "z", min: 120, max: 220, step: 0.5, label: "Z (mm)" },
    { key: "roll", min: -10, max: 10, step: 0.1, label: "Roll (deg)" },
    { key: "pitch", min: -10, max: 10, step: 0.1, label: "Pitch (deg)" },
    { key: "yaw", min: -20, max: 20, step: 0.1, label: "Yaw (deg)" },
  ];

  // Derived IK values for the table (standard React hook outside Canvas)
  const ik = useMemo(() => {
    const p = [pose.x, pose.y, pose.z, pose.roll*DEG2RAD, pose.pitch*DEG2RAD, pose.yaw*DEG2RAD];
    return inverseKinematics({ ...geom }, p);
  }, [geom, pose]);

  const outOfRange = ik.lengthsAbs.some(L => L < limits.lminAbs || L > limits.lmaxAbs);

  return (
    <div className="w-full h-full grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
      {/* Controls */}
      <div className="lg:col-span-1 space-y-4">
        <div className="rounded-2xl p-4 shadow bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Pose</h2>
            <button className="px-3 py-1 rounded-xl border border-white/20" onClick={() => setPose({ x:0, y:0, z:160, roll:0, pitch:0, yaw:0 })}>Reset</button>
          </div>
          <div className="space-y-3">
            {sliders.map(s => (
              <div key={s.key} className="grid grid-cols-7 gap-2 items-center">
                <label className="col-span-3 text-sm opacity-80">{s.label}</label>
                <input
                  type="range"
                  min={s.min}
                  max={s.max}
                  step={s.step}
                  value={pose[s.key]}
                  onChange={(e) => setPose(p => ({ ...p, [s.key]: parseFloat(e.target.value) }))}
                  className="col-span-3"
                />
                <div className="text-right text-sm tabular-nums">{pose[s.key].toFixed(2)}</div>
              </div>
            ))}
            <div className="flex gap-2 items-center">
              <button
                onClick={() => setAnim(a => !a)}
                className={`px-3 py-1 rounded-xl border border-white/20`}
              >{anim ? "Stop" : "Animate"}</button>
            </div>
          </div>
        </div>

        <div className="rounded-2xl p-4 shadow bg-white/5 border border-white/10">
          <h2 className="text-lg font-semibold mb-2">Geometry & Limits</h2>
          <div className="text-sm opacity-80 mb-2">Base radius 120 mm, Platform radius 70 mm, leg pairs (0,1)-(2,3)-(4,5). Edit in code if you want exact anchors.</div>
          <div className="grid grid-cols-2 gap-3 items-center">
            <label className="text-sm opacity-80">Min abs length (mm)</label>
            <input type="number" value={limits.lminAbs}
              onChange={(e)=>setLimits(l=>({...l,lminAbs:parseFloat(e.target.value)}))}
              className="px-2 py-1 rounded bg-white/10 border border-white/20" />
            <label className="text-sm opacity-80">Max abs length (mm)</label>
            <input type="number" value={limits.lmaxAbs}
              onChange={(e)=>setLimits(l=>({...l,lmaxAbs:parseFloat(e.target.value)}))}
              className="px-2 py-1 rounded bg-white/10 border border-white/20" />
          </div>
        </div>

        <div className={`rounded-2xl p-4 shadow border ${outOfRange ? "border-red-500/40 bg-red-500/10" : "border-white/10 bg-white/5"}`}>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Leg Lengths</h2>
            {outOfRange && <span className="text-xs px-2 py-1 rounded-xl bg-red-500/30 border border-red-500/50">Out of range</span>}
          </div>
          <table className="w-full text-sm mt-2">
            <thead className="opacity-70">
              <tr>
                <th className="text-left">Leg</th>
                <th className="text-right">Abs (mm)</th>
                <th className="text-right">Ext (mm)</th>
                <th className="text-center">OK</th>
              </tr>
            </thead>
            <tbody>
              {ik.lengthsAbs.map((L,i)=>{
                const ext = L - geom.l0[i];
                const ok = L >= limits.lminAbs && L <= limits.lmaxAbs;
                return (
                  <tr key={i} className="border-t border-white/10">
                    <td>#{i}</td>
                    <td className="text-right tabular-nums">{L.toFixed(2)}</td>
                    <td className="text-right tabular-nums">{ext.toFixed(2)}</td>
                    <td className="text-center">{ok ? "✓" : "✕"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="rounded-2xl p-4 shadow bg-white/5 border border-white/10">
          <h2 className="text-lg font-semibold mb-2">Self-tests</h2>
          <div className="text-sm opacity-80 mb-2">Console has detailed output. Summary below.</div>
          <div className="flex gap-3 text-sm">
            <span className="px-2 py-1 rounded-xl bg-white/10 border border-white/20">Passed: {tests.passed}</span>
            <span className="px-2 py-1 rounded-xl bg-white/10 border border-white/20">Failed: {tests.failed}</span>
          </div>
          <ul className="mt-2 text-xs space-y-1 opacity-80">
            {tests.details.slice(0,6).map((d,i)=>(<li key={i}>{d}</li>))}
          </ul>
        </div>
      </div>

      {/* 3D View */}
      <div className="lg:col-span-2 h-[70vh] rounded-2xl overflow-hidden border border-white/10 shadow">
        <Canvas camera={{ position: [260, 220, 280], fov: 40 }}>
          <StewartStage pose={pose} anim={anim} geom={geom} onPose={setPose} />
        </Canvas>
      </div>
    </div>
  );
}
