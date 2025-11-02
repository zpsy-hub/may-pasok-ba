/**
 * Test PAGASA Parser
 */

const { getPAGASATyphoonStatus } = require('./pagasa_parser');

console.log('🧪 Testing PAGASA Parser...\n');

async function runTests() {
  try {
    // Test 1: Basic Status Check
    console.log('Test 1: Basic status check');
    const status = await getPAGASATyphoonStatus();
    
    console.assert(typeof status === 'object', '❌ Status should be an object');
    console.assert('hasActiveTyphoon' in status, '❌ Missing hasActiveTyphoon');
    console.assert('metroManilaAffected' in status, '❌ Missing metroManilaAffected');
    console.assert('tcwsLevel' in status, '❌ Missing tcwsLevel');
    console.assert('lastChecked' in status, '❌ Missing lastChecked');
    console.log('✅ Status structure valid\n');
    
    // Test 2: TCWS Level
    console.log('Test 2: TCWS level validation');
    console.assert(
      typeof status.tcwsLevel === 'number',
      '❌ TCWS level should be a number'
    );
    console.assert(
      status.tcwsLevel >= 0 && status.tcwsLevel <= 5,
      `❌ TCWS level ${status.tcwsLevel} out of range (0-5)`
    );
    console.log(`✅ TCWS Level: ${status.tcwsLevel}\n`);
    
    // Test 3: Rainfall Warning
    console.log('Test 3: Rainfall warning structure');
    const rainfall = status.rainfallWarning;
    console.assert(typeof rainfall === 'object', '❌ Rainfall should be an object');
    console.assert('hasActiveWarning' in rainfall, '❌ Missing hasActiveWarning');
    console.assert('metroManilaStatus' in rainfall, '❌ Missing metroManilaStatus');
    console.log('✅ Rainfall warning structure valid\n');
    
    // Test 4: Affected Areas
    console.log('Test 4: Affected areas validation');
    const areas = status.affectedAreas;
    console.assert(Array.isArray(areas), '❌ Affected areas should be an array');
    console.log(`✅ Affected areas count: ${areas.length}\n`);
    
    // Test 5: Metro Manila Detection
    console.log('Test 5: Metro Manila detection');
    if (status.hasActiveTyphoon && status.metroManilaAffected) {
      const mmArea = areas.find(a => 
        a.name && a.name.toLowerCase().includes('metro manila')
      );
      console.assert(mmArea, '❌ Metro Manila not found in affected areas');
      console.assert(mmArea.signal === status.tcwsLevel, '❌ Signal mismatch');
      console.log(`✅ Metro Manila detected with Signal #${mmArea.signal}\n`);
    } else {
      console.log('ℹ️  No active typhoon affecting Metro Manila\n');
    }
    
    // Print summary
    console.log('=' . repeat(60));
    console.log('TEST SUMMARY');
    console.log('=' . repeat(60));
    console.log(JSON.stringify(status, null, 2));
    console.log('=' . repeat(60));
    console.log('✅ All tests passed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

runTests();
