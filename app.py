import os
import scrapy
from flask import Flask, request, jsonify, render_template_string
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from crochet import setup, wait_for

# Set up crochet to run Scrapy asynchronously
setup()

app = Flask(__name__)

# Scrapy Spider for Crypto Scraping
class CryptoSpider(scrapy.Spider):
    name = 'crypto_spider'
    start_urls = ['https://crypto.com/price']

    def parse(self, response):
        rows = response.css('tr.css-1cxc880')

        cryptos = []
        for row in rows[:20]:  # Limit to the first 20 cryptos
            crypto_data = {
                'name': row.css('p.chakra-text.css-rkws3::text').get(),
                'symbol': row.css('span.chakra-text.css-1jj7b1a::text').get(),
                'price': row.css('p.chakra-text.css-13hqrwd::text').get(),
                'market_cap': row.css('td.css-15lyn3l::text')[1].get(),
                'market_grow_24h': row.css('p.chakra-text.css-1okxd::text').get()
            }
            cryptos.append(crypto_data)

        return cryptos

# Function to run Scrapy and return scraped data
@wait_for(20)  # Wait for the result up to 20 seconds
def run_scrapy():
    runner = CrawlerRunner()
    d = runner.crawl(CryptoSpider)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()  # Start the reactor
    return CryptoSpider.cryptos

# API endpoint to get data for the top 20 cryptocurrencies
@app.route('/crypto-api', methods=['GET'])
def get_crypto_data():
    # Run the Scrapy spider and retrieve data
    data = run_scrapy()

    return jsonify(data), 200, {'Content-Type': 'application/json'}

# Home route to render the HTML page
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Live Rates</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f3f4f6;
                margin: 0;
                padding: 20px;
                user-select: none; /* Disable text selection */
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 20px;
            }
            .crypto-table {
                background-color: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .table-header {
                display: flex;
                justify-content: space-between;
                padding: 16px 24px;
                background-color: #f9fafb;
                font-weight: bold;
                color: #4b5563;
            }
            .crypto-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 24px;
                border-top: 1px solid #e5e7eb;
            }
            .crypto-info {
                display: flex;
                align-items: center;
            }
            .crypto-logo {
                width: 32px;
                height: 32px;
                background-color: #e5e7eb;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: #4b5563;
                margin-right: 12px;
            }
            .crypto-name {
                font-weight: bold;
            }
            .crypto-ticker {
                color: #6b7280;
                font-size: 14px;
            }
            .crypto-price {
                text-align: right;
            }
            .price-value {
                font-weight: bold;
            }
            .price-change {
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
            }
            .price-change.positive {
                color: #10b981;
            }
            .price-change.negative {
                color: #ef4444;
            }
            .arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                margin-right: 4px;
            }
            .arrow-up {
                border-bottom: 5px solid #10b981;
            }
            .arrow-down {
                border-top: 5px solid #ef4444;
            }
        </style>
    </head>
    <body oncontextmenu="return false;">
        <div class="container">
            <h1>𝗟𝗜𝗩𝗘 𝗖𝗥𝗬𝗣𝗧𝗢 𝗥𝗔𝗧𝗘𝗦</h1>
            <div class="crypto-table" id="crypto-table">
                <!-- Crypto rates will be populated here -->
            </div>
        </div>

        <script>
    function fetchCryptos() {
        fetch('/crypto-api')
            .then(response => response.json())
            .then(data => {
                // Handle the crypto data and populate HTML
            });
    }

    // Call fetchCryptos() every 1 second
    setInterval(fetchCryptos, 1000);

    window.onload = fetchCryptos;
</script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
