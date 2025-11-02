/**
 * PAGASA Typhoon Bulletin Parser
 * Main orchestrator for fetching, parsing, and aggregating typhoon data
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Optional: Load environment variables
try {
  require('dotenv').config();
} catch (err) {
  // dotenv is optional
}

// Import specialized parsers
const { scrapeRainfallWarning } = require('./scrape_rainfall_warning');
const { scrapeSevereWeatherBulletin } = require('./scrape_severe_weather_bulletin');

// Configuration
const BULLETIN_BASE_URL = process.env.PAGASA_BULLETIN_URL || 
  'https://pubfiles.pagasa.dost.gov.ph/tamss/weather/bulletin/';
const HTTP_TIMEOUT = parseInt(process.env.HTTP_TIMEOUT) || 10000;
const PDF_PARSE_TIMEOUT = parseInt(process.env.PDF_PARSE_TIMEOUT) || 30000;
const ACTIVE_THRESHOLD_HOURS = parseInt(process.env.ACTIVE_TYPHOON_THRESHOLD_HOURS) || 24;
const DEBUG = process.env.DEBUG_MODE === 'true';

// Metro Manila detection keywords
const METRO_MANILA_KEYWORDS = [
  'metro manila', 'ncr', 'national capital region',
  'manila', 'quezon city', 'makati', 'pasig', 'taguig',
  'mandaluyong', 'san juan', 'marikina', 'pasay',
  'paranaque', 'las pinas', 'muntinlupa', 'valenzuela',
  'malabon', 'navotas', 'caloocan', 'pateros'
];

/**
 * Fetch all typhoon bulletins from PAGASA directory
 */
async function getAllBulletinsWithDates() {
  try {
    const response = await axios.get(BULLETIN_BASE_URL, {
      timeout: HTTP_TIMEOUT,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    // Parse HTML directory listing
    const filePattern = /<a href="([^"]*TCB[^"]*\.pdf)">([^<]+)<\/a>\s+(\d{2}-\w{3}-\d{4}\s+\d{2}:\d{2})\s+(\w+)/gi;
    const matches = [...response.data.matchAll(filePattern)];

    const bulletins = [];
    for (const match of matches) {
      const [, href, filename, dateStr, fileSize] = match;
      
      // Parse bulletin metadata
      const bulletinMatch = filename.match(/TCB.*?#(\d+)_([^.]+)/i);
      if (!bulletinMatch) continue;

      const [, number, typhoonName] = bulletinMatch;
      const isFinal = filename.toUpperCase().endsWith('F.PDF');
      
      // Parse date (format: "18-Sep-2025 03:09")
      const fileDate = new Date(dateStr.replace(/-/g, ' '));
      const ageMs = Date.now() - fileDate.getTime();
      const ageHours = ageMs / (1000 * 60 * 60);
      
      bulletins.push({
        filename,
        url: `${BULLETIN_BASE_URL}${encodeURIComponent(href)}`,
        typhoonName: typhoonName.toUpperCase(),
        number: parseInt(number),
        isFinal,
        fileDate: fileDate.toISOString(),
        ageHours: ageHours.toFixed(1),
        ageText: formatAge(ageHours),
        fileSize
      });
    }

    if (DEBUG) {
      console.log(`📋 Found ${bulletins.length} bulletins`);
    }

    return bulletins;
  } catch (error) {
    console.error('❌ Error fetching bulletins:', error.message);
    throw error;
  }
}

/**
 * Format age in human-readable format
 */
function formatAge(hours) {
  if (hours < 1) return `${Math.round(hours * 60)} minutes ago`;
  if (hours < 24) return `${hours.toFixed(1)} hours ago`;
  return `${(hours / 24).toFixed(1)} days ago`;
}

/**
 * Sort bulletins intelligently (by typhoon name, then by bulletin number)
 */
function sortBulletinsIntelligently(bulletins) {
  // Group by typhoon name
  const typhoonGroups = new Map();
  bulletins.forEach(bulletin => {
    if (!typhoonGroups.has(bulletin.typhoonName)) {
      typhoonGroups.set(bulletin.typhoonName, []);
    }
    typhoonGroups.get(bulletin.typhoonName).push(bulletin);
  });

  // Sort typhoon names (Z→A, most recent first)
  const sortedTyphoonNames = Array.from(typhoonGroups.keys()).sort((a, b) => {
    return b.localeCompare(a);
  });

  // Sort bulletins within each typhoon (highest number first)
  const sorted = [];
  sortedTyphoonNames.forEach(name => {
    const typhoonBulletins = typhoonGroups.get(name);
    typhoonBulletins.sort((a, b) => {
      if (a.number !== b.number) return b.number - a.number;
      return new Date(b.fileDate) - new Date(a.fileDate);
    });
    sorted.push(...typhoonBulletins);
  });

  return sorted;
}

/**
 * Find most recent active typhoon
 */
function findMostRecentActiveTyphoon(bulletins) {
  const sorted = sortBulletinsIntelligently(bulletins);

  for (const bulletin of sorted) {
    // Skip if too old
    if (bulletin.ageHours > ACTIVE_THRESHOLD_HOURS) continue;

    // Skip if this is a FINAL bulletin
    if (bulletin.isFinal) continue;

    // Check if typhoon has a more recent FINAL bulletin
    const hasExitedPAR = sorted.find(b =>
      b.typhoonName === bulletin.typhoonName &&
      b.number > bulletin.number &&
      b.isFinal &&
      b.ageHours <= ACTIVE_THRESHOLD_HOURS
    );

    if (hasExitedPAR) continue;

    // Found active typhoon!
    if (DEBUG) {
      console.log(`✅ Active typhoon found: ${bulletin.typhoonName} (Bulletin #${bulletin.number})`);
    }
    return bulletin;
  }

  if (DEBUG) {
    console.log('ℹ️  No active typhoons found');
  }
  return null;
}

/**
 * Parse PDF bulletin using @pagasa-parser/source-pdf
 */
async function parseBulletinPDF(bulletinUrl) {
  let tempPdfPath = null;
  
  try {
    // Download PDF to temp file
    tempPdfPath = path.join(os.tmpdir(), `tcb_${Date.now()}.pdf`);
    const response = await axios({
      method: 'get',
      url: bulletinUrl,
      responseType: 'stream',
      timeout: HTTP_TIMEOUT
    });

    const writer = fs.createWriteStream(tempPdfPath);
    response.data.pipe(writer);

    await new Promise((resolve, reject) => {
      writer.on('finish', resolve);
      writer.on('error', reject);
    });

    if (DEBUG) {
      console.log(`📄 Downloaded PDF: ${tempPdfPath}`);
    }

    // Parse PDF
    const PDFSource = require('@pagasa-parser/source-pdf').default;
    const source = new PDFSource(tempPdfPath);
    
    const parsedData = await Promise.race([
      source.parse(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('PDF parse timeout')), PDF_PARSE_TIMEOUT)
      )
    ]);

    if (DEBUG) {
      console.log('✅ PDF parsed successfully');
    }

    return parsedData;

  } catch (error) {
    console.error('❌ PDF parsing error:', error.message);
    throw error;
  } finally {
    // Cleanup temp file
    if (tempPdfPath && fs.existsSync(tempPdfPath)) {
      try {
        fs.unlinkSync(tempPdfPath);
      } catch (err) {
        // Ignore cleanup errors
      }
    }
  }
}

/**
 * Extract Metro Manila areas from parsed bulletin
 */
function extractMetroManilaFromBulletin(bulletin) {
  const metroManilaAffected = [];

  if (!bulletin || !bulletin.signals) return metroManilaAffected;

  Object.entries(bulletin.signals).forEach(([signalKey, signalData]) => {
    const signalLevel = parseInt(signalKey) + 1; // 0→1, 1→2, etc.

    if (!signalData.areas) return;

    Object.values(signalData.areas).forEach(areaGroup => {
      if (!Array.isArray(areaGroup)) return;

      areaGroup.forEach(area => {
        const areaName = (area.name || '').toLowerCase();
        const isMetroManila = METRO_MANILA_KEYWORDS.some(keyword =>
          areaName.includes(keyword.toLowerCase())
        );

        if (isMetroManila) {
          metroManilaAffected.push({
            name: area.name,
            signal: signalLevel,
            part: area.part || false,
            includes: area.includes || null,
            source: 'BULLETIN_PDF'
          });
        }
      });
    });
  });

  return metroManilaAffected;
}

/**
 * Main function: Get PAGASA typhoon status
 */
async function getPAGASATyphoonStatus() {
  const startTime = Date.now();

  try {
    console.log('🌀 Checking PAGASA typhoon status...');

    // Fetch bulletins and rainfall warning in parallel
    const [allBulletins, rainfallData] = await Promise.all([
      getAllBulletinsWithDates(),
      scrapeRainfallWarning().catch(err => {
        console.warn('⚠️  Rainfall warning scraping failed:', err.message);
        return { hasActiveWarning: false, error: err.message };
      })
    ]);

    // Find active typhoon
    const activeTyphoon = findMostRecentActiveTyphoon(allBulletins);

    if (!activeTyphoon) {
      // No active typhoon
      const result = {
        hasActiveTyphoon: false,
        typhoonStatus: 'NO_TYPHOON',
        metroManilaAffected: false,
        tcwsLevel: 0,
        affectedAreas: [],
        rainfallWarning: rainfallData,
        recentBulletins: allBulletins.slice(0, 5).map(b => ({
          name: b.typhoonName,
          number: b.number,
          date: b.fileDate,
          age: b.ageText,
          isFinal: b.isFinal
        })),
        lastChecked: new Date().toISOString(),
        message: 'No active typhoons affecting the Philippines',
        processingTimeMs: Date.now() - startTime
      };

      return result;
    }

    // Parse active typhoon bulletin
    let affectedAreas = [];
    let tcwsLevel = 0;
    let parsedBulletin = null;

    try {
      parsedBulletin = await parseBulletinPDF(activeTyphoon.url);
      affectedAreas = extractMetroManilaFromBulletin(parsedBulletin);
      tcwsLevel = Math.max(...affectedAreas.map(a => a.signal), 0);

      if (DEBUG) {
        console.log(`📊 Extracted ${affectedAreas.length} Metro Manila areas from PDF`);
      }
    } catch (pdfError) {
      console.warn('⚠️  PDF parsing failed, trying web scraper fallback...');
      
      // Fallback to web scraping
      try {
        const webData = await scrapeSevereWeatherBulletin();
        if (webData.metroManilaAffected) {
          affectedAreas = webData.affectedAreas;
          tcwsLevel = webData.tcwsLevel;
        }
      } catch (webError) {
        console.error('❌ Web scraper fallback also failed:', webError.message);
      }
    }

    // Determine typhoon status
    let typhoonStatus = 'AFFECTING';
    if (activeTyphoon.ageHours < 6) {
      typhoonStatus = 'AFFECTING';
    } else if (activeTyphoon.ageHours < 12) {
      typhoonStatus = 'PASSING';
    } else {
      typhoonStatus = 'EXITING';
    }

    // Build result
    const result = {
      hasActiveTyphoon: true,
      typhoonName: activeTyphoon.typhoonName,
      typhoonStatus,
      bulletinNumber: activeTyphoon.number,
      bulletinDate: activeTyphoon.fileDate,
      bulletinUrl: activeTyphoon.url,
      bulletinAge: activeTyphoon.ageText,
      isFinalBulletin: activeTyphoon.isFinal,
      metroManilaAffected: affectedAreas.length > 0,
      tcwsLevel,
      affectedAreas,
      rainfallWarning: rainfallData,
      recentBulletins: allBulletins.slice(0, 5).map(b => ({
        name: b.typhoonName,
        number: b.number,
        date: b.fileDate,
        age: b.ageText,
        isFinal: b.isFinal
      })),
      lastChecked: new Date().toISOString(),
      message: affectedAreas.length > 0
        ? `Typhoon ${activeTyphoon.typhoonName} is currently affecting Metro Manila (TCWS #${tcwsLevel})`
        : `Typhoon ${activeTyphoon.typhoonName} is active but not affecting Metro Manila`,
      processingTimeMs: Date.now() - startTime
    };

    return result;

  } catch (error) {
    console.error('❌ Fatal error:', error);
    return {
      hasActiveTyphoon: false,
      typhoonStatus: 'ERROR',
      metroManilaAffected: false,
      tcwsLevel: 0,
      affectedAreas: [],
      rainfallWarning: { hasActiveWarning: false },
      lastChecked: new Date().toISOString(),
      error: error.message,
      message: 'Error checking typhoon status',
      processingTimeMs: Date.now() - startTime
    };
  }
}

/**
 * Main execution (when run directly)
 */
async function main() {
  try {
    const status = await getPAGASATyphoonStatus();
    
    // Write to JSON file (project root, not nodejs-pagasa directory)
    const outputPath = path.join(__dirname, '..', 'pagasa_status.json');
    fs.writeFileSync(outputPath, JSON.stringify(status, null, 2));
    
    console.log(`\n✅ Status saved to: ${outputPath}`);
    console.log(`⏱️  Processing time: ${status.processingTimeMs}ms\n`);
    
    // Print summary
    console.log('═'.repeat(60));
    console.log('SUMMARY');
    console.log('═'.repeat(60));
    console.log(status.message);
    if (status.hasActiveTyphoon) {
      console.log(`Typhoon: ${status.typhoonName}`);
      console.log(`Bulletin #${status.bulletinNumber} (${status.bulletinAge})`);
      console.log(`Metro Manila TCWS: Level ${status.tcwsLevel}`);
    }
    if (status.rainfallWarning?.hasActiveWarning) {
      console.log(`⚠️  Rainfall Warning: ${status.rainfallWarning.warningLevel || 'Active'}`);
    }
    console.log('═'.repeat(60));
    
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Export for use as module
module.exports = {
  getPAGASATyphoonStatus,
  getAllBulletinsWithDates,
  findMostRecentActiveTyphoon,
  parseBulletinPDF,
  extractMetroManilaFromBulletin
};

// Run main if executed directly
if (require.main === module) {
  main();
}
