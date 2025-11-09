/**
 * Severe Weather Bulletin Scraper
 * Scrapes TCWS data from PAGASA severe weather bulletin page
 * Updated to properly parse the HTML table structure
 */

const axios = require('axios');
const cheerio = require('cheerio');

const SEVERE_WEATHER_URL = process.env.PAGASA_SEVERE_WEATHER_URL ||
  'https://www.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin';
const HTTP_TIMEOUT = parseInt(process.env.HTTP_TIMEOUT) || 30000;

// Metro Manila detection keywords (case-insensitive)
const METRO_MANILA_KEYWORDS = [
  'metro manila',
  'ncr',
  'national capital region'
];

/**
 * Scrape severe weather bulletin page
 * Properly parses the TCWS table structure from PAGASA bulletin
 */
async function scrapeSevereWeatherBulletin() {
  try {
    console.log('🌐 Scraping PAGASA Severe Weather Bulletin...');
    
    const response = await axios.get(SEVERE_WEATHER_URL, {
      timeout: HTTP_TIMEOUT,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    const $ = cheerio.load(response.data);
    
    // Extract typhoon name from page title/headings
    let typhoonName = null;
    $('h3, h5').each((i, elem) => {
      const text = $(elem).text();
      const match = text.match(/(?:Super\s+)?(?:Typhoon|Tropical\s+Storm|Tropical\s+Depression)\s+"?([A-Z][a-z]+)"?/i);
      if (match) {
        typhoonName = match[1].toUpperCase();
      }
    });

    // Parse TCWS tables
    // Structure: <thead> has signal number (in img filename!), <tbody> has affected areas in <li> tags
    const affectedAreas = [];
    let maxTcwsLevel = 0;

    console.log(`   🔍 Found ${$('thead').length} <thead> elements`);

    $('thead').each((i, thead) => {
      const $thead = $(thead);
      
      // Signal number is in the img filename (e.g., tcws3.png)
      const $img = $thead.find('img');
      const imgSrc = $img.attr('src') || '';
      const signalMatch = imgSrc.match(/tcws(\d+)\.png/i);
      
      if (signalMatch) {
        const signalLevel = parseInt(signalMatch[1]);
        console.log(`   📋 Checking TCWS ${signalLevel}...`);
        
        // Get the tbody that follows this thead
        const $tbody = $thead.next('tbody');
        
        // Find the "Affected Areas" row (first tr with bg-danger td)
        const $affectedRow = $tbody.find('td.bg-danger').first().closest('tr');
        if ($affectedRow.length === 0) {
          console.log(`      ⚠️  No affected areas row found`);
          return;
        }
        
        // Get all list items in the affected areas cell
        const $affectedCell = $affectedRow.find('td').last();
        const allText = $affectedCell.text().toLowerCase();
        const liCount = $affectedCell.find('li').length;
        console.log(`      Found ${liCount} <li> elements in affected areas`);
        
        // Check only the deepest-level li elements (ones that don't contain other li elements)
        let foundInThisSignal = false;
        $affectedCell.find('li').each((j, li) => {
          const $li = $(li);
          
          // Skip if this li contains other li elements (it's just a grouping header)
          if ($li.find('li').length > 0) {
            return; // continue to next
          }
          
          const itemText = $li.text().toLowerCase();
          
          // Check if this specific li mentions Metro Manila
          const hasMetroManila = METRO_MANILA_KEYWORDS.some(keyword =>
            itemText.includes(keyword.toLowerCase())
          );
          
          if (hasMetroManila && !foundInThisSignal) {
            console.log(`   ✅ FOUND: Metro Manila explicitly listed under TCWS ${signalLevel}`);
            
            affectedAreas.push({
              name: 'Metro Manila',
              signal: signalLevel,
              part: false,
              includes: null,
              source: 'HTML_TABLE_IMG'
            });
            maxTcwsLevel = Math.max(maxTcwsLevel, signalLevel);
            foundInThisSignal = true;
          }
        });
      }
    });

    const result = {
      typhoonName,
      metroManilaAffected: affectedAreas.length > 0,
      tcwsLevel: maxTcwsLevel,
      affectedAreas,
      scrapedAt: new Date().toISOString(),
      url: SEVERE_WEATHER_URL
    };

    console.log(`   ℹ️  Typhoon: ${typhoonName || 'N/A'}`);
    console.log(`   ℹ️  Metro Manila TCWS: ${maxTcwsLevel}`);
    console.log(`   ℹ️  Metro Manila Affected: ${result.metroManilaAffected}`);

    return result;

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
