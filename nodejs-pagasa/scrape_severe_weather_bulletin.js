/**
 * Severe Weather Bulletin Scraper
 * Fallback scraper for when PDF parsing fails
 */

const axios = require('axios');
const cheerio = require('cheerio');

const SEVERE_WEATHER_URL = process.env.PAGASA_SEVERE_WEATHER_URL ||
  'https://www.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin';
const HTTP_TIMEOUT = parseInt(process.env.HTTP_TIMEOUT) || 10000;

// Metro Manila detection keywords
const METRO_MANILA_KEYWORDS = [
  'metro manila', 'ncr', 'national capital region'
];

/**
 * Scrape severe weather bulletin page
 */
async function scrapeSevereWeatherBulletin() {
  try {
    const response = await axios.get(SEVERE_WEATHER_URL, {
      timeout: HTTP_TIMEOUT,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    const $ = cheerio.load(response.data);
    
    // Extract typhoon name from headings
    let typhoonName = null;
    $('h1, h2, h3, h4').each((i, elem) => {
      const text = $(elem).text();
      const match = text.match(/(?:Typhoon|Tropical Storm|Tropical Depression)\s+"?([A-Z]+)"?/i);
      if (match) {
        typhoonName = match[1].toUpperCase();
      }
    });

    // Find TCWS tables
    const affectedAreas = [];
    let maxTcwsLevel = 0;

    $('table').each((tableIndex, table) => {
      const $table = $(table);
      
      $table.find('tr').each((rowIndex, row) => {
        const rowText = $(row).text();
        const signalMatch = rowText.match(/Signal\s+No\.\s*(\d+)/i);
        
        if (signalMatch) {
          const signalLevel = parseInt(signalMatch[1]);
          const isMetroManila = METRO_MANILA_KEYWORDS.some(keyword =>
            rowText.toLowerCase().includes(keyword)
          );

          if (isMetroManila) {
            affectedAreas.push({
              name: 'Metro Manila',
              signal: signalLevel,
              part: false,
              includes: null,
              source: 'WEB_SCRAPER_TABLE'
            });
            maxTcwsLevel = Math.max(maxTcwsLevel, signalLevel);
          }
        }
      });
    });

    // Check page text for Metro Manila mentions
    const pageText = $('body').text();
    if (affectedAreas.length === 0) {
      for (let signal = 5; signal >= 1; signal--) {
        const signalPattern = new RegExp(
          `Signal\\s+(?:No\\.?\\s*)?${signal}[\\s\\S]{0,200}(${METRO_MANILA_KEYWORDS.join('|')})`,
          'i'
        );
        if (signalPattern.test(pageText)) {
          affectedAreas.push({
            name: 'Metro Manila',
            signal,
            part: false,
            includes: null,
            source: 'WEB_SCRAPER_TEXT'
          });
          maxTcwsLevel = signal;
          break;
        }
      }
    }

    return {
      typhoonName,
      metroManilaAffected: affectedAreas.length > 0,
      tcwsLevel: maxTcwsLevel,
      affectedAreas,
      scrapedAt: new Date().toISOString(),
      url: SEVERE_WEATHER_URL
    };

  } catch (error) {
    console.error('❌ Severe weather bulletin scraping error:', error.message);
    throw error;
  }
}

module.exports = { scrapeSevereWeatherBulletin };

// Test if run directly
if (require.main === module) {
  scrapeSevereWeatherBulletin()
    .then(data => {
      console.log('Severe Weather Bulletin Data:');
      console.log(JSON.stringify(data, null, 2));
    })
    .catch(err => {
      console.error('Error:', err);
      process.exit(1);
    });
}
