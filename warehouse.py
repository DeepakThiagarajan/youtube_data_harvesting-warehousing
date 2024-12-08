# Importing Necessary Libraries
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
import datetime
import mysql.connector
import isodate

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
            
        st.success(f"Retrieved {len(Comment_data)} comments")
        
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
mysql_database = "youtube_database"
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

# Main Application Logic
def main():
    st.title("YouTube Data Harvesting and Warehousing")

    youtube = Api_connect()
    if not youtube:
        st.stop()
    
    # Enter the channel ID for which the data is to be retrieved
    channel_id = st.text_input("Enter YouTube Channel ID:")
    if not channel_id:
        st.info("Please enter a YouTube Channel ID")
        st.stop()

    conn = connect_to_mysql()    
    if not conn:
        st.error("Failed to connect to database")
        st.stop()

    try:
        create_tables(conn)
        tab1, tab2 = st.tabs(["Data Collection & Storage", "Data Analysis"])    
    
        with tab1:
            if channel_id:
                if st.button("Get Channel Details"):
                    # Fetch Channel Data
                    with st.spinner("Fetching channel information..."):
                        channel_info = get_channel_info(youtube, channel_id)
                        if channel_info:
                            st.session_state.channel_info = channel_info
                            st.header("Channel Information")
                            st.write(channel_info)
                            insert_channel_info_to_mysql(conn, channel_info)

                            # Fetch Video Data
                            video_ids = get_video_ids(youtube, channel_id)
                            if video_ids:
                                video_data = get_Video_Details(youtube, video_ids)
                                if video_data:
                                    st.session_state.video_data = video_data
                                    st.header("Video Information")
                                    st.dataframe(pd.DataFrame(video_data))
                                    insert_video_info_to_mysql(conn, video_data)

                            # Fetch Playlist Data
                            playlist_info = get_playlist_details(youtube, channel_id)
                            if playlist_info:
                                st.session_state.playlist_info = playlist_info
                                st.header("Playlist Information")
                                st.dataframe(pd.DataFrame(playlist_info))
                                insert_playlist_info_to_mysql(conn, playlist_info)

                            st.success("✅ Data collection and storage completed!")

                # Comments Section
                if 'video_data' in st.session_state:
                    st.markdown("---")
                    st.header("📝 Comments Section")
                    
                    # Video selection dropdown
                    video_options = {v['Video_Id']: v['Title'] for v in st.session_state.video_data}
                    selected_video = st.selectbox(
                        "Select Video to View Comments",
                        options=list(video_options.keys()),
                        format_func=lambda x: video_options[x][:100] + "..."  # Truncate long titles
                    )

                    if st.button("Get Comments"):
                        with st.spinner("Fetching comments..."):
                            comments = get_comment_Details(youtube, selected_video)
                            if comments:
                                st.success(f"Found {len(comments)} comments")
                                st.dataframe(pd.DataFrame(comments))
                                insert_comment_info_to_mysql(conn, comments)
                            else:
                                st.info("No comments found for this video")

        with tab2:
            st.header("Data Analysis")
            
            if 'video_data' not in st.session_state or 'channel_info' not in st.session_state:
                st.warning("Please collect channel data first before analyzing")
                st.stop()
            
            # Convert video data to DataFrame
            video_df = pd.DataFrame(st.session_state.video_data)

            numeric_columns = ['Views', 'Likes', 'Comments', 'Favorite_count']
            for col in numeric_columns:
                video_df[col] = pd.to_numeric(video_df[col], errors='coerce')
            
            # 1. Top 10 Videos by Views
            st.subheader("Most Viewed Videos")
            top_videos = video_df.nlargest(10, 'Views')[['Title', 'Views']]
            st.bar_chart(top_videos.set_index('Title'))
            
            # 2. View Count Distribution
            st.subheader("View Count Distribution")
            st.line_chart(video_df['Views'].sort_values(ascending=False))
            
            # 3. Video Statistics
            st.subheader("Video Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Views", f"{video_df['Views'].sum():,}")
            with col2:
                st.metric("Total Likes", f"{video_df['Likes'].sum():,}")
            with col3:
                st.metric("Average Views", f"{int(video_df['Views'].mean()):,}")

            # 4. Video Duration Analysis
            st.subheader("Video Duration Analysis")
            video_df['Duration_Min'] = pd.to_numeric(video_df['Duration']) / 60
            st.line_chart(video_df[['Duration_Min']])
            
            # 5. Comments Analysis
            st.subheader("Comments Distribution")
            st.bar_chart(video_df[['Comments']])
            
            # 6. Publishing Day Analysis
            st.subheader("Publishing Day Analysis")
            video_df['Publishdate'] = pd.to_datetime(video_df['Publishdate'])
            video_df['Publishing_Day'] = video_df['Publishdate'].dt.day_name()
            day_dist = video_df['Publishing_Day'].value_counts()
            st.bar_chart(day_dist)

            # 7. Basic Stats Table
            st.subheader("Basic Statistics")
            stats_df = pd.DataFrame({
                'Metric': ['Total Videos', 'Average Views', 'Average Likes', 'Average Comments'],
                'Value': [
                    len(video_df),
                    int(video_df['Views'].mean()),
                    int(video_df['Likes'].mean()),
                    int(video_df['Comments'].mean())
                ]
            })
            st.table(stats_df)

            # 8. Like-to-View Ratio
            st.subheader("Like-to-View Ratio")
            video_df['Like_to_View_Ratio'] = (video_df['Likes'] / video_df['Views']) * 100
            ratio_df = video_df.nlargest(10, 'Like_to_View_Ratio')[['Title', 'Like_to_View_Ratio']]
            st.bar_chart(ratio_df.set_index('Title'))

            # 9. Views and Likes Over Time
            st.subheader("Trending Views and Likes Over Time")
            video_df['Publishdate'] = pd.to_datetime(video_df['Publishdate'])
            trend_df = video_df.sort_values(by='Publishdate')
            st.line_chart(trend_df.set_index('Publishdate')[['Views', 'Likes']])

            # 10. Duration vs. Engagement
            st.subheader("Duration vs. Engagement")
            st.scatter_chart(video_df, x='Duration_Min', y='Views', size='Likes', color='Comments')

            
            # . Download Option
            st.subheader("Download Analysis Data")
            csv = video_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Complete Data",
                csv,
                "youtube_channel_analysis.csv",
                "text/csv",
                key='download-csv'
            )

            # . Raw Data View
            if st.checkbox("Show Raw Data"):
                st.subheader("Raw Video Data")
                st.dataframe(video_df)                                        
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":    
    main()
