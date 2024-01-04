# Flask Application to Display Twitter Data from SQLite Database
from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Function to get data from SQLite database
def get_twitter_data(time_filter):
    conn = sqlite3.connect('twitter_data_IMG.db')
    cursor = conn.cursor()

    end_date = datetime.now()
    if time_filter == "24h":
        start_date = end_date - timedelta(hours=24)
    elif time_filter == "48h":
        start_date = end_date - timedelta(hours=48)
    elif time_filter == "1w":
        start_date = end_date - timedelta(days=7)
    else:
        start_date = end_date - timedelta(hours=24)  # Default to 24h

    # 更新这里的查询语句，加入 ORDER BY
    query = "SELECT * FROM tweets WHERE created_at BETWEEN ? AND ? ORDER BY created_at DESC"
    cursor.execute(query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return data

# Route to display data
@app.route('/')
def display_data():
    time_filter = request.args.get('time_filter', '24h')
    data = get_twitter_data(time_filter)
    return render_template('twitter_card_front.html', twitter_data=data)
from scraper_twitter import scrape_tweets, save_to_db

@app.route('/scrape')
def scrape():
    ids = [1651448056834056192, 38167656, 272736093, 2465283662, 3178231, 6690032, 155252642]
    print("开始爬取tweets")
    tweets = scrape_tweets(ids)
    print("爬取完成，保存到数据库")
    save_to_db(tweets)
    return "Success"

if __name__ == '__main__':
    app.run(debug=True, host = "0.0.0.0")
