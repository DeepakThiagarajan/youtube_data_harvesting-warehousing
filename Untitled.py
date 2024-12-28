# Importing Necessary Libraries
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
import datetime
import mysql.connector
import isodate
import altair as alt

# API Connection
Api_Key = "AIzaSyCmxcNUjTYT9V3BvJfJ9eCGkzrKqR_XCFM"
Api_Name = "youtube"
Api_Version = "v3"

def Api_connect():
    try:
        youtube = build(Api_Name, Api_Version, developerKey=Api_Key)
        return youtube
    except Exception as e:
        st.error(f"Failed to connect to YouTube API: {e}")
        return None

# Function to get the channel details
def get_channel_info(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id
    )
    response = request.execute()

    data = []
    for i in response["items"]:
        data.append({
            "Channel_Name": i["snippet"]["title"],
            "Channel_Id": i["id"],
            "Subscribers": i["statistics"]["subscriberCount"],
            "Views": i["statistics"]["viewCount"],
            "Total_videos": i["statistics"]["videoCount"],
            "Channel_description": i["snippet"]["description"],
            "Playlist_Id": i["contentDetails"]["relatedPlaylists"]["uploads"]
        })
    return data

# Function to get the video ids
def get_video_ids(youtube, channel_id):
    video_ids = []
    response = youtube.channels().list(
        id=channel_id,
        part='contentDetails'
    ).execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])

        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return video_ids

# Function to get the Video Details
def get_Video_Details(youtube, video_ids):
    Video_data = []
    try:
        for video_id in video_ids:
            try:
                request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=video_id
                )
                response = request.execute()

                for item in response["items"]:
                    data = {
                        'Channel_Name': item['snippet']['channelTitle'],
                        'Channel_Id': item['snippet']['channelId'],
                        'Video_Id': item['id'],
                        'Title': item['snippet']['title'],
                        'Tags': item['snippet'].get('tags', []),
                        'Thumbnail': item['snippet']['thumbnails']['default']['url'],
                        'Description': item['snippet'].get('description', ''),
                        'Publishdate': datetime.datetime.strptime(
                            item['snippet']['publishedAt'], 
                            '%Y-%m-%dT%H:%M:%SZ'
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'Duration': str(isodate.parse_duration(
                            item['contentDetails']['duration']
                        ).total_seconds()),
                        'Views': item['statistics'].get('viewCount', 0),
                        'Likes': item['statistics'].get('likeCount', 0),
                        'Comments': item['statistics'].get('commentCount', 0),
                        'Favorite_count': item['statistics'].get('favoriteCount', 0),
                        'Definition': item['contentDetails'].get('definition', ''),
                        'Caption_Status': item['contentDetails'].get('caption', '')
                    }
                    Video_data.append(data)
            except Exception as e:
                st.warning(f"Error fetching details for video {video_id}: {e}")
                continue
    except Exception as e:
        st.error(f"Failed to get video details: {e}")
    return Video_data

# Function to get Comment Details
def get_comment_Details(youtube, video_id, max_comments=10):
    """
    Fetch top comments for a specific video.
    Args:
        youtube: YouTube API connection object
        video_id: Single video ID to fetch comments from
        max_comments: Number of comments to fetch (default 10)
    Returns:
        List of comments
    """
    Comment_data = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            publish_date = datetime.datetime.strptime(
                comment['publishedAt'], 
                '%Y-%m-%dT%H:%M:%SZ'
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            Comment_data.append({
                'Comment_id': item['id'],
                'Video_id': video_id,
                'Comment_text': comment['textDisplay'],
                'Comment_Author': comment['authorDisplayName'],
                'Comment_Published': publish_date
            })
            
        print(f"Retrieved {len(Comment_data)} comments")
        
    except Exception as e:
        st.error(f"Error fetching comments: {str(e)}")
    
    return Comment_data

# Function to get Playlist Details
def get_playlist_details(youtube, channel_id):
    next_page_token = None
    All_data = []
    while True:
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            data = {
                'Playlist_Id': item['id'],
                'Title': item['snippet']['title'],
                'Channel_Id': item['snippet']['channelId'],
                'Channel_Name': item['snippet']['channelTitle'],
                'PublishedAt': item['snippet']['publishedAt'],
                'Video_count': item['contentDetails']['itemCount']
            }
            All_data.append(data)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return All_data

# MySQL connection configuration
mysql_host = "localhost"
mysql_user = "root"
mysql_password = "simple"
mysql_database = "youtube_db"
mysql_port = "3306"

# Function to connect to MySQL database
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            port=mysql_port
        )
        print("Connected to MySQL database successfully")
        return conn
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

# Function to create tables in MySQL
def create_tables(conn):
    cursor = conn.cursor()

    queries = {
        "channel_data": """
            CREATE TABLE IF NOT EXISTS channel_data (
                Channel_Name VARCHAR(255),
                Channel_Id VARCHAR(255) PRIMARY KEY,
                Subscribers BIGINT,
                Views BIGINT,
                Total_videos INT,
                Channel_description TEXT,
                Playlist_Id VARCHAR(255)
            )
        """,
        "video_data": """
            CREATE TABLE IF NOT EXISTS video_data (
                Channel_Name VARCHAR(255),
                Channel_Id VARCHAR(255),
                Video_Id VARCHAR(255) PRIMARY KEY,
                Title VARCHAR(255),
                Tags TEXT,
                Thumbnail TEXT,
                Description TEXT,
                Publishdate DATETIME,  # Consistent naming
                Duration VARCHAR(255),
                Views BIGINT,
                Likes BIGINT,
                Comments INT,
                Favorite_count INT,
                Definition VARCHAR(255),
                Caption_Status VARCHAR(255)
            )
        """,
        "playlist_data": """
            CREATE TABLE IF NOT EXISTS playlist_data (
                Playlist_Id VARCHAR(255) PRIMARY KEY,
                Title VARCHAR(255),
                Channel_Id VARCHAR(255),
                Channel_Name VARCHAR(255),
                Publishdate DATETIME,  # Consistent naming
                Video_count INT
            )
        """,
        "comment_data": """
            CREATE TABLE IF NOT EXISTS comment_data (
                Comment_id VARCHAR(255) PRIMARY KEY,
                Video_id VARCHAR(255),
                Comment_text TEXT,
                Comment_Author VARCHAR(255),
                Comment_Published DATETIME
            )
        """
    }
    for query in queries.values():
        cursor.execute(query)
    conn.commit()
    cursor.close()

# Functions to insert data into MySQL tables
def insert_channel_info_to_mysql(conn, channel_info):
    cursor = conn.cursor()
    try:
        for info in channel_info:
            insert_query = """
            INSERT INTO channel_data (Channel_Name, Channel_Id, Subscribers, Views, Total_videos, Channel_description, Playlist_Id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Channel_Name = VALUES(Channel_Name),
                Subscribers = VALUES(Subscribers),
                Views = VALUES(Views),
                Total_videos = VALUES(Total_videos),
                Channel_description = VALUES(Channel_description),
                Playlist_Id = VALUES(Playlist_Id)
            """
            cursor.execute(insert_query, (
                info["Channel_Name"],
                info["Channel_Id"],
                info["Subscribers"],
                info["Views"],
                info["Total_videos"],
                info["Channel_description"],
                info["Playlist_Id"]
            ))
        
        conn.commit()
        print("Channel info inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting channel info into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

def insert_video_info_to_mysql(conn, video_info):
    cursor = conn.cursor()
    try:
        for info in video_info:
            insert_query = """
            INSERT INTO video_data (Channel_Name, Channel_Id, Video_Id, Title, Tags, Thumbnail, Description, Publishdate, Duration, Views, Likes, Comments, Favorite_count, Definition, Caption_Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Title = VALUES(Title),
                Tags = VALUES(Tags),
                Thumbnail = VALUES(Thumbnail),
                Description = VALUES(Description),
                Publishdate = VALUES(Publishdate),
                Duration = VALUES(Duration),
                Views = VALUES(Views),
                Likes = VALUES(Likes),
                Comments = VALUES(Comments),
                Favorite_count = VALUES(Favorite_count),
                Definition = VALUES(Definition),
                Caption_Status = VALUES(Caption_Status)
            """
            cursor.execute(insert_query, (
                info["Channel_Name"],
                info["Channel_Id"],
                info["Video_Id"],
                info["Title"],
                ', '.join(info["Tags"]) if info["Tags"] else None,
                info["Thumbnail"],
                info["Description"],
                info["Publishdate"],
                info["Duration"],
                info["Views"],
                info["Likes"],
                info["Comments"],
                info["Favorite_count"],
                info["Definition"],
                info["Caption_Status"]
            ))
        
        conn.commit()
        print("Video info inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting video info into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

def insert_comment_info_to_mysql(conn, comment_info):
    cursor = conn.cursor()
    try:
        for info in comment_info:
            insert_query = """
            INSERT INTO comment_data (Comment_id, Video_id, Comment_text, Comment_Author, Comment_Published)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Comment_text = VALUES(Comment_text),
                Comment_Author = VALUES(Comment_Author),
                Comment_Published = VALUES(Comment_Published)
            """
            cursor.execute(insert_query, (
                info["Comment_id"],
                info["Video_id"],
                info["Comment_text"],
                info["Comment_Author"],
                info["Comment_Published"]
            ))
        
        conn.commit()
        print("Comment info inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting comment info into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

def insert_playlist_info_to_mysql(conn, playlist_info):
    cursor = conn.cursor()
    try:
        for info in playlist_info:
            insert_query = """
            INSERT INTO playlist_data (Playlist_Id, Title, Channel_Id, Channel_Name, PublishedAt, Video_count)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                Title = VALUES(Title),
                Channel_Id = VALUES(Channel_Id),
                Channel_Name = VALUES(Channel_Name),
                PublishedAt = VALUES(PublishedAt),
                Video_count = VALUES(Video_count)
            """
            cursor.execute(insert_query, (
                info["Playlist_Id"],
                info["Title"],
                info["Channel_Id"],
                info["Channel_Name"],
                info["PublishedAt"],
                info["Video_count"]
            ))
        
        conn.commit()
        print("Playlist info inserted into MySQL successfully!")
    except mysql.connector.Error as e:
        print("Error inserting playlist info into MySQL:", e)
        conn.rollback()
    finally:
        cursor.close()

def get_stored_channel_list(conn):
    """Fetch list of all channels stored in the database"""
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT Channel_Name, Channel_Id, Subscribers, Total_videos 
        FROM channel_data 
        ORDER BY Channel_Name
        """
        cursor.execute(query)
        channels = cursor.fetchall()
        return channels
    except mysql.connector.Error as e:
        st.error(f"Error fetching stored channels: {e}")
        return []
    finally:
        cursor.close()


def fetch_stored_channel_data(conn, channel_id):
    """Fetch all data for a specific channel from database"""
    cursor = conn.cursor(dictionary=True)
    data = {
        'channel_info': [],
        'video_data': [],
        'playlist_info': [],
        'comment_data': []
    }
    
    try:
        # Fetch channel info
        cursor.execute("SELECT * FROM channel_data WHERE Channel_Id = %s", (channel_id,))
        data['channel_info'] = cursor.fetchall()
        
        if not data['channel_info']:
            st.error(f"No channel found with ID: {channel_id}")
            return None
            
        # Fetch video info
        cursor.execute("SELECT * FROM video_data WHERE Channel_Id = %s", (channel_id,))
        data['video_data'] = cursor.fetchall()
        
        # Fetch playlist info
        cursor.execute("SELECT * FROM playlist_data WHERE Channel_Id = %s", (channel_id,))
        data['playlist_info'] = cursor.fetchall()
        
        # Fetch comments for this channel's videos
        if data['video_data']:
            video_ids = [video['Video_Id'] for video in data['video_data']]
            placeholders = ', '.join(['%s'] * len(video_ids))
            comment_query = f"SELECT * FROM comment_data WHERE Video_id IN ({placeholders})"
            cursor.execute(comment_query, tuple(video_ids))
            data['comment_data'] = cursor.fetchall()
        
        return data
        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        cursor.close()  

# SQL Analysis Functions

def get_channel_videos(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT channel_data.Channel_Name, video_data.Title as Video_Name
            FROM video_data 
            JOIN channel_data ON channel_data.Channel_Id = video_data.Channel_Id
            ORDER BY channel_data.Channel_Name
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_videos_per_channel(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT DISTINCT Channel_Name, COUNT(Video_Id) as Total_Videos 
            FROM video_data 
            GROUP BY Channel_Name 
            ORDER BY Total_Videos DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_top_viewed_videos(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Channel_Name, Title as Video_Name, Views as Total_Views
            FROM video_data
            ORDER BY Views DESC
            LIMIT 10
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_comment_counts(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Title as Video_Name, Comments as Total_Comments
            FROM video_data
            ORDER BY Comments DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_highest_likes_by_channel(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT v.Channel_Name, v.Title as Video_Name, v.Likes as Highest_Likes
            FROM video_data v
            INNER JOIN (
                SELECT Channel_Id, MAX(Likes) as max_likes
                FROM video_data
                GROUP BY Channel_Id
            ) vm ON v.Channel_Id = vm.Channel_Id AND v.Likes = vm.max_likes
            ORDER BY v.Likes DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_video_likes(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Title as Video_Name, Likes
            FROM video_data
            ORDER BY Likes DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_channel_views(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Channel_Name, Views as Total_Views
            FROM channel_data
            ORDER BY Views DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_2022_channels(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT DISTINCT Channel_Name
            FROM video_data
            WHERE YEAR(Publishdate) = 2022
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_avg_duration(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Channel_Name,
                   TIME_FORMAT(
                       SEC_TO_TIME(AVG(CAST(Duration AS DECIMAL(10,2)))), 
                       '%H:%i:%s'
                   ) as Average_Duration
            FROM video_data
            GROUP BY Channel_Name
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()

def get_most_commented_videos(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT Channel_Name, Title as Video_Name, Comments as Total_Comments
            FROM video_data
            ORDER BY Comments DESC
        ''')
        result = cursor.fetchall()
        df = pd.DataFrame(result)
        df.index += 1
        return df
    finally:
        cursor.close()
  

# Main Application Logic
def main():
    st.set_page_config(page_title='YouTube Data Harvesting and Warehousing',
                    layout='wide',
                    initial_sidebar_state='expanded')

    youtube = Api_connect()
    if not youtube:
        st.stop()

    conn = connect_to_mysql()    
    if not conn:
        st.error("Failed to connect to database")
        st.stop()

    try:
        create_tables(conn)

        st.header("🛠️ Channel Management")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ Add New Channel")
            new_channel_id = st.text_input("Enter YouTube Channel ID:")
            
        with col2:
            st.subheader("🗃️ View Stored Channels")
            if st.button("🔃 Refresh Channel List"):
                stored_channels = get_stored_channel_list(conn)
                if stored_channels:
                    st.session_state.stored_channels = stored_channels
                    st.success(f"Found {len(stored_channels)} stored channels")
                else:
                    st.info("No channels found in database")

        # Display stored channels in an expander
        if 'stored_channels' in st.session_state:
            with st.expander("View Stored Channels"):
                for channel in st.session_state.stored_channels:
                    cols = st.columns([3, 2, 2, 1])
                    with cols[0]:
                        st.write(f"📺 {channel['Channel_Name']}")
                    with cols[1]:
                        st.write(f"🔔 {channel['Subscribers']:,} subs")
                    with cols[2]:
                        st.write(f"📽️ {channel['Total_videos']} videos")
                    with cols[3]:
                        if st.button("Load", key=f"btn_{channel['Channel_Id']}"):
                            st.session_state.selected_channel_id = channel['Channel_Id']
                            st.session_state.selected_channel_name = channel['Channel_Name']              
                                        
        channel_id = new_channel_id or st.session_state.get('selected_channel_id', '')

        tab1, tab2, tab3 = st.tabs(["📦 Data Collection & Storage", "📊 Data Analysis", "📈 Data Visualization"])    
    
        with tab1:
            if channel_id:
                if st.button("Get Channel Details"):
                    # Fetch Channel Data
                    with st.spinner("Fetching channel information..."):
                        channel_info = get_channel_info(youtube, channel_id)
                        if channel_info:
                            st.session_state.channel_info = channel_info
                            st.header("📺Channel Information")
                            st.write(channel_info)
                            insert_channel_info_to_mysql(conn, channel_info)

                            # Fetch Video Data
                            video_ids = get_video_ids(youtube, channel_id)
                            if video_ids:
                                video_data = get_Video_Details(youtube, video_ids)
                                if video_data:
                                    st.session_state.video_data = video_data
                                    st.header("📽️ Video Information")
                                    st.dataframe(pd.DataFrame(video_data))
                                    insert_video_info_to_mysql(conn, video_data)

                            # Fetch Playlist Data
                            playlist_info = get_playlist_details(youtube, channel_id)
                            if playlist_info:
                                st.session_state.playlist_info = playlist_info
                                st.header("📃 Playlist Information")
                                st.dataframe(pd.DataFrame(playlist_info))
                                insert_playlist_info_to_mysql(conn, playlist_info)


                # Comments Section
                if 'video_data' in st.session_state:
                    st.markdown("---")
                    st.header("🗨️ Comments Section")
                    
                    # Video selection dropdown
                    video_options = {v['Video_Id']: v['Title'] for v in st.session_state.video_data}
                    selected_video = st.selectbox(
                        "Select Video to View Comments",
                        options=list(video_options.keys()),
                        format_func=lambda x: video_options[x][:100] + "..."
                    )

                    if st.button("Get Comments"):
                        with st.spinner("Fetching comments..."):
                            comments = get_comment_Details(youtube, selected_video)
                            if comments:
                                st.dataframe(pd.DataFrame(comments))
                                insert_comment_info_to_mysql(conn, comments)
                            else:
                                st.info("No comments found for this video")

                            st.success("✅ Data collection and storage completed!")    

        with tab2:
            st.header("Data Analysis")
            st.subheader("Analysis using SQL")
            
            st.markdown('''You can analyze the YouTube channel data stored in the MySQL database.
                        Select a question below to see the analysis results in a table format.''')
            
            Questions = [
                'Select your Question',
                '1. What are the names of all the videos and their corresponding channels?',
                '2. Which channels have the most number of videos, and how many videos do they have?',
                '3. What are the top 10 most viewed videos and their respective channels?',
                '4. How many comments were made on each video, and what are their corresponding video names?',
                '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
                '6. What is the total number of likes for each video, and what are their corresponding video names?',
                '7. What is the total number of views for each channel, and what are their corresponding channel names?',
                '8. What are the names of all the channels that have published videos in the year 2022?',
                '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
                '10. Which videos have the highest number of comments, and what are their corresponding channel names?'
            ]
            
            selected_question = st.selectbox(' ', options=Questions)
            
            if selected_question.startswith('1.'):
                df = get_channel_videos(conn)
                st.dataframe(df)
            
            elif selected_question.startswith('2.'):
                df = get_videos_per_channel(conn)
                st.dataframe(df)
                st.bar_chart(df.set_index('Channel_Name')['Total_Videos'])
            
            elif selected_question.startswith('3.'):
                df = get_top_viewed_videos(conn)
                st.dataframe(df)
                st.bar_chart(df.set_index('Video_Name')['Total_Views'])
            
            elif selected_question.startswith('4.'):
                df = get_comment_counts(conn)
                st.dataframe(df)
                st.bar_chart(df.head(10).set_index('Video_Name')['Total_Comments'])
            
            elif selected_question.startswith('5.'):
                df = get_highest_likes_by_channel(conn)
                st.dataframe(df)
                st.bar_chart(df.set_index('Video_Name')['Highest_Likes'])
            
            elif selected_question.startswith('6.'):
                st.write('**:red[Note]: Dislike counts are no longer available as they were made private by YouTube in December 2021.**')
                df = get_video_likes(conn)
                st.dataframe(df)
                st.bar_chart(df.head(10).set_index('Video_Name')['Likes'])
            
            elif selected_question.startswith('7.'):
                df = get_channel_views(conn)
                st.dataframe(df)
                st.bar_chart(df.set_index('Channel_Name')['Total_Views'])
            
            elif selected_question.startswith('8.'):
                df = get_2022_channels(conn)
                st.dataframe(df)
            
            elif selected_question.startswith('9.'):
                df = get_avg_duration(conn)
                st.dataframe(df)
            
            elif selected_question.startswith('10.'):
                df = get_most_commented_videos(conn)
                st.dataframe(df)
                st.bar_chart(df.head(10).set_index('Video_Name')['Total_Comments'])

        with tab3:
            st.header("Data Visualization")
            
            if 'video_data' not in st.session_state or 'channel_info' not in st.session_state:
                st.warning("Please collect channel data first before analyzing")
                st.stop()

            Option = st.selectbox('Select Visualization', [
                'Select to view',
                '1. Channels with Subscriber Count',
                '2. Channels with highest No Of Videos',
                '3. Channels with Total Views',
                '4. Channels with Average videos duration',
                '5. Year wise Performance Analysis',
                '6. Advanced Analytics Dashboard'
            ])

            if Option == '1. Channels with Subscriber Count':
                def plot_subscribers():
                    query = '''SELECT Channel_Name, Subscribers 
                            FROM channel_data 
                            ORDER BY Subscribers DESC'''
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data)
                    st.subheader("Channel Subscriber Counts")
                    st.bar_chart(df.set_index('Channel_Name')['Subscribers'])
                    st.dataframe(df)
                    cursor.close()
                plot_subscribers()

            elif Option == '2. Channels with highest No Of Videos':
                def plot_video_counts():
                    query = '''SELECT Channel_Name, Total_videos 
                            FROM channel_data 
                            ORDER BY Total_videos DESC'''
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data)
                    st.subheader("Total Videos per Channel")
                    st.bar_chart(df.set_index('Channel_Name')['Total_videos'])
                    st.dataframe(df)
                    cursor.close()
                plot_video_counts()  

            elif Option == '3. Channels with Total Views':
                def plot_channel_views():
                    query = '''SELECT Channel_Name, Views 
                            FROM channel_data 
                            ORDER BY Views DESC'''
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data)
                    st.subheader("Total Views per Channel")
                    st.bar_chart(df.set_index('Channel_Name')['Views'])
                    st.dataframe(df)
                    cursor.close()
                plot_channel_views()

            elif Option == '4. Channels with Average videos duration':
                def plot_avg_duration():
                    query = '''SELECT 
                                Channel_Name,
                                AVG(CAST(Duration AS DECIMAL(10,2))) as Avg_Duration_Seconds,
                                TIME_FORMAT(
                                    SEC_TO_TIME(AVG(CAST(Duration AS DECIMAL(10,2)))), 
                                    '%H:%i:%s'
                                ) as Avg_Duration_Formatted
                            FROM video_data
                            GROUP BY Channel_Name'''
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data)
                    st.subheader("Average Video Duration by Channel")
                
                    st.bar_chart(df.set_index('Channel_Name')['Avg_Duration_Seconds'])
                    st.write("Average Duration (HH:MM:SS)")
                    for _, row in df.iterrows():
                        st.write(f"{row['Channel_Name']}: {row['Avg_Duration_Formatted']}")
                    cursor.close()
                plot_avg_duration()

            elif Option == '5. Year wise Performance Analysis':
                def plot_yearly_performance():
                    query = '''SELECT 
                                YEAR(Publishdate) as Year,
                                Channel_Name,
                                COUNT(Video_Id) as Total_Videos,
                                SUM(Likes) as Total_Likes,
                                SUM(Views) as Total_Views,
                                SUM(Comments) as Total_Comments
                            FROM video_data
                            GROUP BY Channel_Name, YEAR(Publishdate)
                            ORDER BY Year'''
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query)
                    data = cursor.fetchall()
                    df = pd.DataFrame(data)
                    
                    st.subheader("Yearly Video Uploads")
                    yearly_videos = df.pivot(index='Year', columns='Channel_Name', values='Total_Videos')
                    st.line_chart(yearly_videos)
                    
                    likes_chart = alt.Chart(df).mark_bar().encode(
                        x='Year:O',
                        y='Total_Likes:Q',
                        color='Channel_Name:N',
                        tooltip=['Year', 'Channel_Name', 'Total_Likes']
                    ).properties(
                        title='Yearly Likes by Channel',
                        width=600,
                        height=400
                    )
                    
                    views_chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X('Year:O', title='Year'),
                        y=alt.Y('Total_Views:Q', title='Total Views'),
                        xOffset='Channel_Name:N',  # This creates the grouping
                        color='Channel_Name:N',
                        tooltip=['Year', 'Channel_Name', 'Total_Views']
                    ).properties(
                        title='Yearly Views by Channel',
                        width=600,
                        height=400
                    )

                    comments_plot = alt.Chart(df).mark_line(point=True).encode(
                        x=alt.X('Year:O', title='Year'),
                        y=alt.Y('Total_Comments:Q', title='Total Comments'),
                        color='Channel_Name:N',
                        tooltip=['Year', 'Channel_Name', 'Total_Comments']
                    ).properties(
                        title='Yearly Comments by Channel (Connected Scatter)',
                        width=600,
                        height=400
                    )
    
                    st.subheader("Yearly Performance Analysis")
                    st.altair_chart(likes_chart, use_container_width=True)
                    st.altair_chart(views_chart, use_container_width=True)
                    st.altair_chart(comments_plot, use_container_width=True)
                    
                    st.dataframe(df)
                    cursor.close()
                plot_yearly_performance()

            elif Option == '6. Advanced Analytics Dashboard':
                video_df = pd.DataFrame(st.session_state.video_data)
                
                # Convert numeric columns
                numeric_columns = ['Views', 'Likes', 'Comments', 'Favorite_count']
                for col in numeric_columns:
                    video_df[col] = pd.to_numeric(video_df[col], errors='coerce')
                
                # Key metrics
                st.subheader("Channel Overview")
                st.write(f"📺 {channel['Channel_Name']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Views", f"{video_df['Views'].sum():,}")
                with col2:
                    st.metric("Total Likes", f"{video_df['Likes'].sum():,}")
                with col3:
                    st.metric("Average Views", f"{int(video_df['Views'].mean()):,}")

                # Most viewed videos
                st.subheader("Top 10 Most Viewed Videos")
                top_videos = video_df.nlargest(10, 'Views')[['Title', 'Views', 'Channel_Name']]
                st.bar_chart(top_videos.set_index('Title')['Views'])
                st.dataframe(top_videos)

                # Engagement metrics over time
                st.subheader("Engagement Trends")
                video_df['Publishdate'] = pd.to_datetime(video_df['Publishdate'])
                engagement_df = video_df.sort_values('Publishdate').set_index('Publishdate')
                st.line_chart(engagement_df[['Views', 'Likes', 'Comments']])

                # Video duration analysis
                st.subheader("Video Duration Analysis")
                video_df['Duration_Min'] = pd.to_numeric(video_df['Duration']) / 60
                st.line_chart(video_df[['Duration_Min']])
                
                # Publishing patterns
                st.subheader("Publishing Patterns")
                video_df['Publishing_Day'] = video_df['Publishdate'].dt.day_name()
                day_counts = video_df['Publishing_Day'].value_counts()
                st.bar_chart(day_counts)                                   
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":    
    main()
