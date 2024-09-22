# youtube_data_harvesting-warehousing
**Introduction**
This project aims to provide an easy-to-use interface for harvesting data from YouTube channels and storing it in a MySQL database. The data collected includes channel information, video details, comments, and playlists. The project is built using Python, Streamlit, and MySQL.

**Features**
YouTube API Integration: Collect data from YouTube channels, including channel statistics, video details, comments, and playlists.
Data Storage: Store the harvested data in a MySQL database for further analysis and exploration.
Streamlit Interface: User-friendly interface for inputting channel IDs, storing data, and searching the database.
Real-time Data Retrieval: Retrieve and store data in real-time, ensuring up-to-date information.
Search Functionality: Search the MySQL database for specific channel data using keywords.

**Prerequisites**
Before running this project, ensure you have the following installed:
Python 3.x
MySQL Server
Streamlit
Required Python libraries

**Configuration**
API Key:
  Obtain a YouTube Data API key from the Google Developer Console.
  Replace the placeholder Api_Key in the script with your API key.
Database Configuration:
  Ensure your MySQL credentials and database details are correctly configured in the script.

**Database Schema**
The MySQL database consists of the following tables:
  channel_data: Stores general information about YouTube channels.Channel_Name, Channel_Id, Subscribers, Views, Total_videos, Channel_description, Playlist_Id
  video_data: Stores details about each video on the channel.
  Channel_Name, Channel_Id, Video_Id, Title, Tags, Thumbnail, Description, Publishdate, Duration, Views, Likes, Comments, Favorite_count, Definition, Caption_Status
  comment_data: Stores top-level comments on each video.
  Comment_id, Video_id, Comment_text, Comment_Author, Comment_Published
  playlist_data: Stores details about playlists on the channel.
  Playlist_Id, Title, Channel_Id, Channel_Name, PublishedAt, Video_count

  ![image](https://github.com/user-attachments/assets/88d47ab4-62b8-4d58-8d18-7de124f2dc59)




