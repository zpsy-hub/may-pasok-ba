/**
 * Rainfall Warning Scraper
 * Scrapes PAGASA NCR rainfall warning page
 */

const axios = require('axios');
const cheerio = require('cheerio');

const RAINFALL_URL = process.env.PAGASA_RAINFALL_URL ||
  'https://www.pagasa.dost.gov.ph/regional-forecast/ncrprsd';
const HTTP_TIMEOUT = parseInt(process.env.HTTP_TIMEOUT) || 10000;

/**
 * Scrape rainfall warning from PAGASA NCR page
 */
async function scrapeRainfallWarning() {
  try {
    const response = await axios.get(RAINFALL_URL, {
      timeout: HTTP_TIMEOUT,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    const $ = cheerio.load(response.data);
    let fullText = '';
    
    // Find rainfall warning section
    $('#rainfalls .tab-content .tab-pane').each((i, pane) => {
      const paneText = $(pane).text();
      if (paneText.includes('Heavy Rainfall Warning') || paneText.includes('RAINFALL')) {
        fullText += paneText + '\n';
      }
    });

    // Also check for any warning tables
    $('#rainfalls table').each((i, table) => {
      fullText += $(table).text() + '\n';
    });

    if (!fullText.trim()) {
      return {
        hasActiveWarning: false,
        warningLevel: null,
        warningNumber: null,
        warningTitle: null,
        issuedAt: null,
        weatherSystem: null,
        affectedAreas: [],
        metroManilaStatus: 'NO WARNING',
        hazards: [],
        nextWarningAt: null,
        fullText: null,
        scrapedAt: new Date().toISOString()
      };
    }

    // Extract warning details
    const warningNumMatch = fullText.match(/Heavy Rainfall Warning No\.\s*(\d+)/i);
    const warningNum = warningNumMatch ? parseInt(warningNumMatch[1]) : null;

    const issuedMatch = fullText.match(/Issued at:\s*([^\\n]+)/i);
    const issuedAt = issuedMatch ? issuedMatch[1].trim() : null;

    const weatherSystemMatch = fullText.match(/Weather System:\s*([^\\n]+)/i);
    const weatherSystem = weatherSystemMatch ? weatherSystemMatch[1].trim() : null;

    // Extract warning levels
    const warnings = {
      RED: /RED WARNING LEVEL:\s*([^.]+)/i,
      ORANGE: /ORANGE WARNING LEVEL:\s*([^.]+)/i,
      YELLOW: /YELLOW WARNING LEVEL:\s*([^.]+)/i
    };

    const affectedAreas = [];
    let highestWarningLevel = null;
    let metroManilaStatus = 'NO WARNING';

    for (const [level, pattern] of Object.entries(warnings)) {
      const match = fullText.match(pattern);
      if (match) {
        const areas = match[1].trim();
        affectedAreas.push({
          warningLevel: level,
          areas
        });

        if (!highestWarningLevel) {
          highestWarningLevel = level;
        }

        // Check if Metro Manila is mentioned
        if (areas.toLowerCase().includes('metro manila') || 
            areas.toLowerCase().includes('ncr')) {
          metroManilaStatus = `${level} WARNING`;
        }
      }
    }

    // Extract hazards
    const hazards = [];
    if (fullText.toLowerCase().includes('flooding')) hazards.push('FLOODING');
    if (fullText.toLowerCase().includes('landslide')) hazards.push('LANDSLIDE');
    if (fullText.toLowerCase().includes('flash flood')) hazards.push('FLASH_FLOOD');

    // Extract next warning time
    const nextWarningMatch = fullText.match(/next warning.{0,20}(\d{1,2}:\d{2}\s*(?:AM|PM))/i);
    const nextWarningAt = nextWarningMatch ? nextWarningMatch[1].trim() : null;

    return {
      hasActiveWarning: affectedAreas.length > 0,
      warningLevel: highestWarningLevel,
      warningNumber: warningNum,
      warningTitle: `Heavy Rainfall Warning No. ${warningNum}`,
      issuedAt,
      weatherSystem,
      affectedAreas,
      metroManilaStatus,
      hazards,
      nextWarningAt,
      fullText: fullText.substring(0, 500), // Truncate for size
      scrapedAt: new Date().toISOString()
    };

  } catch (error) {
    console.error('❌ Rainfall warning scraping error:', error.message);
    throw error;
  }
}

module.exports = { scrapeRainfallWarning };

// Test if run directly
if (require.main === module) {
  scrapeRainfallWarning()
    .then(data => {
      console.log('Rainfall Warning Data:');
      console.log(JSON.stringify(data, null, 2));
    })
    .catch(err => {
      console.error('Error:', err);
      process.exit(1);
    });
}
