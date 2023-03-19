#!/usr/bin/env python
# coding: utf-8

#Google API
from googleapiclient.discovery import build

#Data cleaning and analysis
import pandas as pd
import numpy as np
import isodate
from dateutil import parser

#Display and data visualisation

from IPython.display import JSON
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
sns.set(style="darkgrid", color_codes=True)


#NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
from wordcloud import WordCloud


# ## 2. Data Creation with Youtube API
api_key = 'AIzaSyA7u5HqUScNk_yL--DPbXj_3ZGHEFnd6Eo'

channel_ids = ["UCR1c65UsjpaVgcLKa7eM1tg", #Les'Copaque
               "UCr9QW8w8CvVAe3MSWZCAn-Q", #Didi dan friends
               "UCfqDvjXc2jbAzaeqlIggkkg", #Monsta
               "UC42ZduLx6o3Nqg04kMuMCEw", #Ejen Ali
               "UCiZL26ScfRZDdEAkkPJgJbA", #Omar dan Hana
              ]

api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(api_service_name, api_version, developerKey = api_key )


def get_channel_stats(youtube, channel_ids):
    
    all_data = []
    request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=','.join(channel_ids))
    response = request.execute() 
    
    for i in range(len(response['items'])):
        data = dict(channelName = response['items'][i]['snippet']['title'],
                    subscribers = response['items'][i]['statistics']['subscriberCount'],
                    views = response['items'][i]['statistics']['viewCount'],
                    totalVideos = response['items'][i]['statistics']['videoCount'],
                    playlistId = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'])
        all_data.append(data)
    
    return pd.DataFrame(all_data)



def get_video_ids(youtube , playlist_id):
    
    video_ids = []
    
    request = youtube.playlistItems().list(
            part = "snippet,contentDetails",
            playlistId = playlist_id,
            maxResults = 50
            )
    response = request.execute()
    
    for item in response ['items']:
        video_ids.append(item['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
            request = youtube.playlistItems().list(
                    part = "contentDetails",
                    playlistId = playlist_id,
                    maxResults = 50,
                    pageToken = next_page_token)
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
            
    return video_ids



def get_video_details(youtube, video_ids):
    
    all_video_info = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute() 

        for video in response['items']:
            stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                             'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                             'contentDetails': ['duration', 'definition', 'caption']
                            }
            video_info = {}
            video_info['video_id'] = video['id']

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)
            
    return pd.DataFrame(all_video_info)


def get_comments_in_videos(youtube, video_ids):
    all_comments = []
    
    for video_id in video_ids:
        try:
            request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId = video_id
            )
            response = request.execute()

            comments_in_video = [comment['snippet']['topLevelComment']['snippet']['textOriginal'] for comment in response['items' [0:10]]
            comments_in_video_info = {"video_id": video_id, "comments": comments_in_video}

            all_comments.append(comments_in_video_info)
        
        except: 
            
            continue
           # print('Could not get comments for video ' + video_id)
            
    return pd.DataFrame(all_comments)                                            


#Test using one playlist id 
request = youtube.playlistItems().list(
        part = "snippet,contentDetails",
        playlistId = "UUr9QW8w8CvVAe3MSWZCAn-Q")
response = request.execute()
           
JSON(response)

video_ids = get_video_ids(youtube, playlist_id)
len(video_ids)

request = youtube.videos().list(
       part ="snippet,contentDetails,statistics",
       id = video_ids [0:5]
   )
response = request.execute()

JSON(response)

video_df = get_video_details(youtube, video_ids)
comments_df = get_comments_in_videos(youtube, video_ids)
comments_df
comments_df['comments'][0]


# ### Get Channel Statistics
channel_data = get_channel_stats(youtube, channel_ids)
channel_data

# Convert count columns to numeric columns
numeric_cols = ['subscribers', 'views', 'totalVideos']
channel_data[numeric_cols] = channel_data[numeric_cols].apply(pd.to_numeric, errors='coerce')

sns.set(rc={'figure.figsize':(10,8)})
ax = sns.barplot(x='channelName', y='subscribers', data=channel_data.sort_values('subscribers', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
plot = ax.set_xticklabels(ax.get_xticklabels())

ax = sns.barplot(x='channelName', y='views', data=channel_data.sort_values('views', ascending=False))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x/1000) + 'K'))
plot = ax.set_xticklabels(ax.get_xticklabels())


# ### Get Video Statistics from all channel and append all together
# Create a dataframe with video statistics and comments from all channels
channel_data = get_channel_stats(youtube,channel_ids)
video_df = pd.DataFrame()
comments_df = pd.DataFrame()

for c in channel_data['channelName'].unique():
    print("Getting video information from channel: " + c)
    playlist_id = channel_data.loc[channel_data['channelName']== c, 'playlistId'].iloc[0]
    video_ids = get_video_ids(youtube, playlist_id)
    
    # get video data
    video_data = get_video_details(youtube, video_ids)
    # get comment data
    comments_data = get_comments_in_videos(youtube, video_ids)

    # append video data together and comment data toghether
    video_df = video_df.append(video_data, ignore_index=True)
    comments_df = comments_df.append(comments_data, ignore_index=True)

video_df


# # Analysis Ideas
# ## Data Cleaning & processing

video_df.isnull().any()

video_df.dtypes

video_df.publishedAt.sort_values().value_counts()


cols = ['viewCount' , 'likeCount', 'favouriteCount', 'commentCount']
video_df[cols] = video_df[cols].apply(pd.to_numeric, errors = 'coerce', axis = 1)

#published day in week(parser libraries)

video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x : parser.parse(x))
video_df['pushblishDayName'] = video_df['publishedAt'].apply(lambda x : x.strftime("%A"))


# #### Convert duration to seconds
# - import isodate
video_df['durationSecs'] = video_df['duration'].apply(lambda x : isodate.parse_duration(x))
video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')

video_df[['duration', 'durationSecs']]

# Add number of tags
video_df['tagsCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))


# Comments and likes per 1000 view ratio
video_df['likeRatio'] = video_df['likeCount']/ video_df['viewCount'] * 1000
video_df['commentRatio'] = video_df['commentCount']/ video_df['viewCount'] * 1000

# Title character length
video_df['titleLength'] = video_df['title'].apply(lambda x: len(x))

video_df.head()


# ## Exploratory Data Analysis

# - import seaborn as sns
# - import matplotlib.pyplot as plt

# ### View distribution per channel

plt.rcParams['figure.figsize'] = (18, 6)
sns.violinplot(video_df['channelTitle'], video_df['viewCount'], palette = 'pastel')
plt.title('Views per channel', fontsize = 14)
plt.show()


# ### Views vs likes and comments

# #### Does the number of likes and comments matter for a video to get more views?

fig, ax = plt.subplots(1,2)
sns.scatterplot( data = video_df, x = 'commentCount', y = 'viewCount', ax = ax[0])
sns.scatterplot( data = video_df, x = 'likeCount', y = 'viewCount', ax = ax[1])

fig, ax = plt.subplots(1,2)
sns.scatterplot(data = video_df, x = "commentRatio", y = "viewCount", ax=ax[0])
sns.scatterplot(data = video_df, x = "likeRatio", y = "viewCount", ax=ax[1])


# ### Video duration

sns.histplot(data = video_df, x = 'durationSecs', bins = 30)


# ### Does the video duration matter for views and interaction (likes/ comments)?

sns.histplot(data=video_df[video_df['durationSecs'] < 10000], x="durationSecs", bins=30)

fig, ax = plt.subplots(1,2)
sns.scatterplot(data = video_df, x = "durationSecs", y = "commentCount", ax=ax[0])
sns.scatterplot(data = video_df, x = "durationSecs", y = "likeCount", ax=ax[1])


# ### Does title lengths matters?

sns.scatterplot(data = video_df, x = "titleLength", y = "viewCount")


# ### Wordcloud for words in title

stop_words = set(stopwords.words('english'))
video_df['title_no_stopwords'] = video_df['title'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in video_df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words) 



def plot_cloud(wordcloud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud) 
    plt.axis("off");

wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', 
                      colormap='viridis', collocations=False).generate(all_words_str)
plot_cloud(wordcloud)

sns.scatterplot(data = video_df, x = "tagsCount", y = "viewCount")


day_df = pd.DataFrame(video_df['pushblishDayName'].value_counts())
weekdays = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_df = day_df.reindex(weekdays)
ax = day_df.reset_index().plot.bar(x='index', y='pushblishDayName', rot=0)


#NLP
from wordcloud import WordCloud

stop_words = set(stopwords.words('indonesian'))
comments_df['comments_no_stopwords'] = comments_df['comments'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in comments_df['comments_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words) 

wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', 
                      colormap='viridis', collocations=False).generate(all_words_str)
plot_cloud(wordcloud)







