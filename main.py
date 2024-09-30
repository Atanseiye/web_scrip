from __future__ import print_function
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import googleapiclient
import pandas as pd
from datetime import datetime
from secret import API_KEY
import requests
import re
import os
import pickle
import io





######### Setting up the Youtube API ###########
# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)


# Function to extract video ID
def extract_video_id(urls:list[str], api_key:str) -> list:

    # Regular expression to extract YouTube video ID
    youtube_regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S*|\S*[\?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    IDs = []
    try:
        for url in urls:
            match = re.search(youtube_regex, url)
            if match:
                IDs.append(match.group(1))
            else:
                IDs.append('Looks like this is not a youtube link')
        print('Done with video ID extraction...')
        # Check for the status code of the API_KEY
        '''
        print(f'{urls[0]}&key={api_key}')
        response = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={IDs[0]}&key={api_key}')
        if response.status_code == 403:
            return "API key is suspended or invalid."

            '''
        return IDs
    except:
        return 'Unknown error. Please, check the link'


# to remove special characters that are not supportted in excel
def clean_excel_string(s):
    if not isinstance(s, str):
        return s  # Return the value unchanged if it's not a string

    # Remove control characters (ASCII codes 0-31)
    cleaned_string = ''.join(c for c in s if ord(c) >= 32)

    # Remove special characters not allowed in Excel sheet names
    # These characters are: : / \ ? * [ ]
    cleaned_string = re.sub(r'[:/\\?\*\[\]]', '', cleaned_string)

    return cleaned_string



# Function to get the channel ID from a video ID
def channel_ids(video_id:list[str]) -> list[str]:

    channel_id = []
    for ids in video_id:
        request = youtube.videos().list(
            part="snippet",
            id=ids
        )

        response = request.execute()
        channel_id.append(response['items'][0]['snippet']['channelId'])
        print('Done with channel ID extraction...')

    return channel_id


# Function to get the channel's upload playlist ID
def get_uploads_playlist_id(channel_ids: list[str]) -> list[str]:
    uploads_playlist_id = []
    for channel_id in channel_ids:
        request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        uploads_playlist_id.append(response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
        print('Done with getting channel playlist ID...')

    return uploads_playlist_id


# Function to get all video IDs from the uploads playlist
def videos_from_playlist(playlist_ids):
    all_playlists_videos = []  # This will store all lists of videos per playlist

    for playlist_id in playlist_ids:
        videos = []  # This will store the videos from a single playlist
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50
        )

        while request:
            response = request.execute()

            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                videos.append(video_id)  # Append each video ID to the videos list

            # Check if there's a next page of results
            if 'nextPageToken' in response:
                request = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=response['nextPageToken']
                )
            else:
                break

        # After fetching all videos from the playlist, append to the master list
        all_playlists_videos.append(videos)

    return all_playlists_videos


import pandas as pd

def comments_from_channels(video_ids_per_channel):
    all_videos_data = {}  # This will store DataFrames for each video

    # Loop through each channel's videos
    for channel_videos in video_ids_per_channel:
        
        # Loop through each video in the current channel
        for video_id in channel_videos:
            video_data = {
                'videoId': video_id,
                'videoLink': f"https://www.youtube.com/watch?v={video_id}",
                'comments': []
            }
            
            try:
                # Fetch comments for the video
                request = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    maxResults=100,
                    textFormat='plainText'
                )

                while request:
                    response = request.execute()

                    for item in response['items']:
                        comment_snippet = item['snippet']['topLevelComment']['snippet']
                        comment_data = {
                            'comment': comment_snippet['textDisplay'],
                            'username': comment_snippet['authorDisplayName'],
                            'likes': comment_snippet['likeCount'],
                            'publishedAt': comment_snippet['publishedAt'],
                            'replies': []
                        }

                        # Check if there are replies to the comment
                        if 'replies' in item:
                            for reply in item['replies']['comments']:
                                reply_snippet = reply['snippet']
                                reply_data = {
                                    'reply': reply_snippet['textDisplay'],
                                    'username': reply_snippet['authorDisplayName'],
                                    'likes': reply_snippet['likeCount'],
                                    'publishedAt': reply_snippet['publishedAt']
                                }
                                comment_data['replies'].append(reply_data)

                        video_data['comments'].append(comment_data)  # Append comment data

                    # Check if there's a next page of comments
                    if 'nextPageToken' in response:
                        request = youtube.commentThreads().list(
                            part='snippet,replies',
                            videoId=video_id,
                            maxResults=100,
                            pageToken=response['nextPageToken'],
                            textFormat='plainText'
                        )
                    else:
                        break

            except googleapiclient.errors.HttpError as e:
                error_reason = e.resp.get('reason', '')
                # Check if the error is related to comments being disabled
                if error_reason == 'commentsDisabled':
                    print(f"Comments are disabled for video: {video_id}")
                else:
                    print(f"Comment disabled here")

            # Create a DataFrame for the video and its comments
            comments_list = []
            for comment in video_data['comments']:
                comment_entry = {
                    'videoId': video_data['videoId'],
                    'videoLink': video_data['videoLink'],
                    'comment': comment['comment'],
                    'username': comment['username'],
                    'likes': comment['likes'],
                    'publishedAt': comment['publishedAt'],
                    'replies': comment['replies']  # Store replies as is
                }
                comments_list.append(comment_entry)

            # Create a DataFrame and store it in the dictionary by video_id
            if comments_list:  # Only create DataFrame if there are comments
                df_video = pd.DataFrame(comments_list)
                all_videos_data[video_id] = df_video

    return all_videos_data

def save_dataframes_to_excel(all_videos_data, filename):
    # Save each video DataFrame to a separate sheet in an Excel file
    with pd.ExcelWriter(filename) as writer:
        for video_id, df in all_videos_data.items():
            df.to_excel(writer, sheet_name=video_id, index=False)

    print("DataFrames saved to 'comments_by_video.xlsx' with separate sheets for each video.")


def save_dataframes_to_csv(all_videos_data, folder_name):
    # Create the folder if it doesn't exist
    os.makedirs(folder_name, exist_ok=True)

    # Save each video DataFrame to a separate CSV file
    for video_id, df in all_videos_data.items():
        # Construct the full file path
        file_path = os.path.join(folder_name, f"{video_id}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8')

