# **YouTube Data Harvesting and Warehousing**  

## **Introduction**  
This project provides an easy-to-use interface for harvesting and storing data from YouTube channels in a MySQL database. The data collected includes channel information, video details, comments, and playlists. The application is built using **Python**, **Streamlit**, and **MySQL**, enabling efficient data analysis and exploration.  

---

## **Features**  

1. **YouTube API Integration**  
   - Retrieve data from YouTube channels, including channel statistics, video details, comments, and playlists.  

2. **Data Storage**  
   - Store the harvested data in a **MySQL database** for further analysis and exploration.  

3. **Streamlit Interface**  
   - User-friendly interface for inputting channel IDs, storing data, and searching the database.  

4. **Real-time Data Retrieval**  
   - Ensure up-to-date information by retrieving and storing data in real-time.  

5. **Search Functionality**  
   - Search the MySQL database for specific channel data using keywords.  

---

## **Prerequisites**  

Before running this project, ensure you have the following installed:  
- **Python 3.x**  
- **MySQL Server**  
- **Streamlit**  
- Required Python libraries  

---

## **Configuration**  

1. **API Key**  
   - Obtain a **YouTube Data API key** from the [Google Developer Console](https://console.cloud.google.com/).  
   - Replace the placeholder `Api_Key` in the script with your API key.  

2. **Database Configuration**  
   - Ensure your MySQL credentials and database details are correctly configured in the script.  

---

## **Database Schema**  

The MySQL database consists of the following tables:  

1. **channel_data**  
   - Stores general information about YouTube channels.  
   - **Columns**:  
     - `Channel_Name`  
     - `Channel_Id`  
     - `Subscribers`  
     - `Views`  
     - `Total_videos`  
     - `Channel_description`  
     - `Playlist_Id`  

2. **video_data**  
   - Stores details about each video on the channel.  
   - **Columns**:  
     - `Channel_Name`  
     - `Channel_Id`  
     - `Video_Id`  
     - `Title`  
     - `Tags`  
     - `Thumbnail`  
     - `Description`  
     - `Publishdate`  
     - `Duration`  
     - `Views`  
     - `Likes`  
     - `Comments`  
     - `Favorite_count`  
     - `Definition`  
     - `Caption_Status`  

3. **comment_data**  
   - Stores top-level comments on each video.  
   - **Columns**:  
     - `Comment_id`  
     - `Video_id`  
     - `Comment_text`  
     - `Comment_Author`  
     - `Comment_Published`  

4. **playlist_data**  
   - Stores details about playlists on the channel.  
   - **Columns**:  
     - `Playlist_Id`  
     - `Title`  
     - `Channel_Id`  
     - `Channel_Name`  
     - `PublishedAt`  
     - `Video_count`  

---

## **How to Run the Project**  

1. Clone the repository.  
2. Install the required Python libraries.
3. streamlit run .warehousing.py

---

## **Sample Output**

![image](https://github.com/user-attachments/assets/3c2337b5-bf0e-4188-b857-0130d28589bb)

![image](https://github.com/user-attachments/assets/50cc60d5-1c3c-477a-bac6-09a4bd51e038)





