// Test JSX syntax

function TestComponent() {
  const geometryParams = { platRadius: 80, baseRadius: 120 };
  
  return (
    <div>
      {/* Validation warnings */}
      {geometryParams.platRadius >= geometryParams.baseRadius && (
        <div className="mb-3 p-2 rounded bg-yellow-900/30 border border-yellow-700 text-yellow-200 text-sm">
          ⚠️ Platform radius cannot be larger than base radius. Value will be automatically adjusted.
        </div>
      )}
    </div>
  );
}

console.log('JSX syntax test passed');
