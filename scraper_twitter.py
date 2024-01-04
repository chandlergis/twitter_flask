import os
import requests
import sqlite3
import pandas as pd
from twitter.scraper import Scraper
from twitter.util import find_key
image_save_dir = './photo_list'
def download_image(image_url, tweet_id, index):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image_path = os.path.join(image_save_dir, f"{tweet_id}_{index}.jpg")
            with open(image_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return image_path
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")
        return None  
def scrape_tweets(ids):
  # 初始化Scraper
  email = 'hyhgoodboy@outlook.com'
  username = '@hyhgoodboy233'
  password = 'h13117855518'
  scraper = Scraper(email, username, password)

  # 获取tweets JSON数据
  tweets_json = scraper.tweets(ids, limit=1)
  # 解析JSON
  tweet_data = []
  for d in tweets_json:
    instructions = find_key(d, 'instructions').pop()
    entries = find_key(instructions, 'entries').pop()
    for entry in entries:
        legacy = find_key(entry, 'legacy')
        for tweet in legacy:
            # 对于每个推文，独立检查和提取媒体信息
            media_info = {
                'media_url_https': None,
                'media_type': None
            }
            if 'extended_entities' in tweet:
                media_list = tweet['extended_entities'].get('media', [])
                if media_list:
                    media_info['media_url_https'] = [media['media_url_https'] for media in media_list if 'media_url_https' in media]
                    media_info['media_type'] = [media['type'] for media in media_list if 'type' in media]
            # 将媒体信息添加到推文数据中
            tweet.update(media_info)
            tweet_data.append(tweet)
            user_key = 'can_dm'  # filter using arbitrary key that only users have
            tweets = (x for x in tweet_data for k in x if k != user_key)
  return tweets
def save_to_db(tweets):
    cols = [
        'user_id_str',
        'id_str',
        'created_at',
        'favorite_count',
        'bookmark_count',
        'full_text',
        'quote_count',
        'reply_count',
        'media_url_https',
        'media_type',
        'lang'
    ]
    tweet_df  = pd.DataFrame(tweets)[cols]
    tweet_df['created_at'] = pd.to_datetime(tweet_df['created_at'], format="%a %b %d %H:%M:%S %z %Y")
    numeric = [
        'favorite_count',
        'quote_count',
        'reply_count',
        'bookmark_count'

    ]
    tweet_df[numeric] = tweet_df[numeric].apply(pd.to_numeric, errors='coerce')

    ## drop duplicates, sort by date
    tweet_df = (tweet_df
        .dropna(subset='id_str')
        .drop_duplicates(subset='id_str')
        .sort_values('created_at', ascending=False)
        .reset_index(drop=True)
        )
  
    # 连接数据库
    conn = sqlite3.connect('twitter_data_IMG.db')
    for index, row in tweet_df.iterrows():
        media_urls = row['media_url_https']
        if media_urls:
            local_image_paths = []
            for i, url in enumerate(media_urls):
                local_path = download_image(url, row['id_str'], i)
                if local_path:
                    local_image_paths.append(local_path)
            local_image_paths_str = ','.join(local_image_paths)
        else:
            local_image_paths_str = ""
        cursor = conn.cursor()
        created_at_str = row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(row['created_at']) else None

        media_urls = row['media_url_https']
        if not isinstance(media_urls, list):
            media_urls = [media_urls] if media_urls else []
            # 使用join连接列表中的URL，如果列表为空，则存储空字符串
        media_urls_str = ','.join(media_urls)
            # 处理media_type
        media_types = row['media_type']
        if not isinstance(media_types, list):
            media_types = [media_types] if media_types else []
        media_types_str = ','.join(media_types)
        cursor.execute('''
        INSERT INTO tweets (user_id_str, id_str, created_at, favorite_count, bookmark_count, full_text, quote_count, reply_count, media_url_https, media_type, lang,local_image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_str) DO NOTHING
        ''', (row['user_id_str'], row['id_str'], created_at_str, row['favorite_count'], row['bookmark_count'], row['full_text'], row['quote_count'], row['reply_count'],media_urls_str, media_types_str, row['lang'],local_image_paths_str))
        cursor.close()

    # 提交事务
    conn.commit()

    # 最后关闭数据库连接
    conn.close()

    print("Tweets saved to database successfully!")