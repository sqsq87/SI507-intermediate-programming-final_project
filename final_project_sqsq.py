#!/usr/bin/env python
# coding: utf-8



from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import random
import plotly.graph_objects as go
import plotly
from plotly.graph_objs import Scatter,Layout
import plotly
import plotly.offline as py
import numpy as np
import plotly.graph_objs as go
import sys
from api import api_key, map_box_access_token_key

#api_key='ufHdikUwcW07Rn3G6GDl6BE_InasbqEZ77r7pZNl5JEB1v3aGEzQt6TTVoaFbw1woysuPhmDcDmIu1Q0oyNcTJvZr9orrdbXRUOVvr9ZnZpEHy_GkDhGgNNJnr9mYHYx'
#map_box_access_token_key='pk.eyJ1Ijoic3FzcSIsImEiOiJja252amp1ZDEwMzR0Mndyczl4ZmF2YTU4In0.5AIAYgPvGswcHlWzjOK5jA'
CACHE_FILE_NAME= 'fp_cache.json'
HEADER=headers = {'Authorization': 'Bearer %s' % api_key, 'User_agent':'Qi Sun'}
CACHE_DICT={}
import sqlite3
con = sqlite3.connect("final_project.db")
cur = con.cursor()

def load_cache():
    '''load the cache
    
    Parameters
    ----------
    None
    Returns
    -------
    dict
        the cache in the python type of dict
    '''
    try:
        cache_file=open(CACHE_FILE_NAME, 'r')
        cache_file_contents=cache_file.read()
        cache=json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache={}
    return cache

def save_cache(cache):
    '''save the cache
    
    Parameters
    ----------
    dict
        the cache to be saved
    Returns
    -------
    none
    '''
    cache_file=open(CACHE_FILE_NAME,'w')
    contents_to_write=json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_use_cache(url,cache, params='none',headers=HEADER, merchant_id='none'):
    '''make the request with the help of cache
    
    Parameters
    ----------
    url: string
        the url of the request
    cache: dict
        the saved cache in the python type of dict
    params: dict 
        the parameters required to be sent to the API
    merchant_id: int
        the id of the merchant, it is used during crawling
    Returns
    -------
    string
        the response text
    '''
    if (params=='none'):
        if ((url+str(merchant_id)) in cache.keys()):
            print('Using cache')
            return (True,cache[url+str(merchant_id)])
        else:
            print('Fetching')
            rep=requests.get(url)
            cache[url+str(merchant_id)]=rep.text
            save_cache(cache)
            return (False, cache[url+str(merchant_id)])
    else:
        if ((url+str(params)) in cache.keys()):
            print('Using cache')
            return (True, cache[url+str(params)])
        else: 
            print('Fetching')
            rep=requests.get(url,params=params,headers=headers)
            cache[url+str(params)]=json.loads(rep.text)
            save_cache(cache)
            return (False, cache[url+str(params)]  ) 
    
def input_menu_and_comment(merchant_id, url):
    '''
    get the menu and comment based on the url
    if the html text is in the cache, use cache
    if not, make another request
    After getting them, input them into the database 'menu' and 'review'
    
    Parameters
    ----------
    merchant_id: int
        the id of the merchant
    url: string
        the url of the request
    
    Returns
    -------
    none
    '''
    
    input_to_database, rep_text=make_url_request_use_cache(url,CACHE_DICT, params='none', headers=HEADER, merchant_id=merchant_id)
    all_menu_text=[]
    comment = []
    if input_to_database==False:
        try:
            

            soup=BeautifulSoup(rep_text, 'html.parser')

            temp=soup.find_all('div',class_='scrollContainer__373c0__3nnaG border-color--default__373c0__2oFDT nowrap__373c0__1_N1j')
            all_menu=temp[0].find_all('p',class_='css-1p0j9vc')

            for i in all_menu:
                all_menu_text.append(i.text.strip())
            insert_data_menu=[]
            for i in range(len(all_menu_text)):
                insert_data_menu.append((int(merchant_id), all_menu_text[i]))
            with con:
                sql='''INSERT INTO menu (merchant_id, menu) VALUES (?,?);'''
                cur.executemany(sql,insert_data_menu)
        except:
            pass
            



        try:
            comment_all=soup.find_all(
                    'p', class_='comment__373c0__1M-px css-n6i4z7')
            comment.append(comment_all[0].text.strip())
            comment.append(comment_all[1].text.strip())
            comment.append(comment_all[2].text.strip())
            insert_data_review=[]
            for i in range(len(comment)):
                insert_data_review.append((int(merchant_id), comment[i]))
            with con:
                sql='''INSERT INTO review (merchant_id, review) VALUES (?,?);'''
                cur.executemany(sql,insert_data_review)
        except:
            pass
    
def calculate_score(cache_dict):
    '''get the score of each restaurants based on
    its review counts and rating
    
    Parameters
    ----------
    cache_dict: dict
        the dict of restaurants with their information get from the API request
    
    Returns
    -------
    list
        a list of scores
    '''
    all_businesses = cache_dict['businesses']
    rating_sum = 0
    for i in range(len(all_businesses)):
        rating_sum = rating_sum + all_businesses[i]['rating']
    all_score = []
    for i in range(len(all_businesses)):
        rating = all_businesses[i]['rating']
        review_counts = all_businesses[i]['review_count']
        score = (review_counts / (review_counts + 200)) * rating + (
            200 / (review_counts + 200)) * rating_sum
        all_score.append(score)
    return all_score

def print_menu_and_reviews(name, menu, review):
    '''print the menu and review of a restaurant
    
    Parameters
    ----------
    name:string
        the name of the merchant
    menu: list
        the list of menus
    review: list
        the list of reviews
    
    Returns
    -------
    none
    '''
    print(name)
    print('MENU:')
    index1=1
    for i in menu:
        print(str(index1)+': '+i)
        index1=index1+1
    index2=1
    print('TOP REVIEWS:')
    for i in review:
        print(str(index2)+': '+i)
        index2=index2+1


def plot_map(merchant_table):
    '''plot the map which represents the location of each recommended restaurant
    
    Parameters
    ----------
    merchant_table:dataframe
        the dataframe which contains the information like id, address, phone of each restaurant
    
    Returns
    -------
    none
    '''
    mapbox_access_token = map_box_access_token_key
    display_text_map = []
    for i in range(len(merchant_table)):
        display_text_map.append(
            'ID:'+ str(merchant_table['id'][i]) + '   NAME: '+ merchant_table['name'][i] +
            '   ADDRESS:' + merchant_table['address'][i] + '   PHONE:' +
            str(merchant_table['phone'][i]) + '   SCORE:' +
            str(round(merchant_table['score'][i], 2)))
    fig = go.Figure(
        go.Scattermapbox(lat=merchant_table['latitude'],
                         lon=merchant_table['longitude'],
                         mode='markers',
                         marker=go.scattermapbox.Marker(
                             size=14, color=1 / merchant_table['score']),
                         text=display_text_map,
                         hoverinfo='text'))

    fig.update_layout(hovermode='closest',
                      mapbox=dict(accesstoken=mapbox_access_token,
                                  bearing=0,
                                  center=go.layout.mapbox.Center(lat=40.7,
                                                                 lon=-74.0),
                                  pitch=0,
                                  zoom=9))

    fig.show()


def plot_bar(merchant_table):
    '''plot the map which represents the score of each recommended restaurant
    
    Parameters
    ----------
    merchant_table:dataframe
        the dataframe which contains the information like id, address, phone of each restaurant
    
    Returns
    -------
    none
    '''
    plotly.offline.init_notebook_mode(connected=True)
    display_text_bar = []
    for i in range(len(merchant_table)):
        display_text_bar.append(
            'ID:'+ str(merchant_table['id'][i]) + '   NAME: '+ merchant_table['name'][i] +
            '   ADDRESS:' + merchant_table['address'][i] + '   PHONE:' +
            str(merchant_table['phone'][i]) + '   SCORE:' +
            str(round(merchant_table['score'][i], 2)))
            
    trace0 = go.Bar(x=merchant_table['name'],
                    y=merchant_table['score'],
                    name='the score of the recommended restaurants',
                    marker=dict(color='rgb(49,130,189)'),
                    text=display_text_bar,
                    hoverinfo='text')
    data = [trace0]
    py.iplot(data)

def plot_table(recommendation_table):
    '''plot the table to represent the information of each recommended restaurant
    
    Parameters
    ----------
    recommendation_table:dataframe
        the dataframe which contains the information like id, address, phone of each restaurant
    
    Returns
    -------
    none
    '''
    fig = go.Figure(data=[
        go.Table(header=dict(
            values=list(['id','name','address','phone','score']), fill_color='paleturquoise', align='left'),
                 cells=dict(values=[
                     recommendation_table['id'], recommendation_table['name'],
                     recommendation_table['address'], 
                     recommendation_table['phone'],
                     round(recommendation_table['score'],1)
                 ],
                            fill_color='lavender',
                            align='left'))
    ])

    fig.show()


def plot_scatter(merchant_table):
    '''plot the scatter plot which represents the score of each recommended restaurant
    
    Parameters
    ----------
    merchant_table:dataframe
        the dataframe which contains the information like id, address, phone of each restaurant
    
    Returns
    -------
    none
    '''
    plotly.offline.init_notebook_mode(connected=True)
    display_text_scatter = []
    for i in range(len(merchant_table)):
        display_text_scatter.append('ID:' + str(merchant_table['id'][i]) +
                                    '   NAME: ' + merchant_table['name'][i] +
                                    '   ADDRESS:' +
                                    merchant_table['address'][i] +
                                    '   PHONE:' +
                                    str(merchant_table['phone'][i]) +
                                    '   SCORE:' +
                                    str(round(merchant_table['score'][i], 2)))

    trace0 = go.Scatter(x=recommendation_table['name'],
                        y=recommendation_table['score'],
                        mode='markers',
                        text=display_text_scatter,
                        hoverinfo='text',
                        marker=dict(size=recommendation_table['score'] / 2))
    data = [trace0]
    py.iplot(data)


def write_into_merchant(term,category, location,  cache_current):
    '''write the information of the merchants into the database 'merchant'
    
    Parameters
    ----------
    cache_current: dict
        the dict returned from the API request or already stored in the cache
    term: string
        the term of the restaurants according to the user request
    category:string
        'restaurant'
    location:string
        the location of the restaurants according to the user request
    
    
    Returns
    -------
    none
    '''
    index = 0
    score = calculate_score(cache_current)
    insert_data = []
    for i in cache_current['businesses']:
        insert_data.append(
            (i['name'], i['location']['display_address'][0],
             i['coordinates']['latitude'], i['coordinates']['longitude'],
             i['rating'], i['review_count'], i['display_phone'], score[index],
             term, category, location,i['url']))
        index = index + 1

    sql = '''INSERT INTO MERCHANT (merchant_name, address, latitude, longitude, rating, review_count, phone, score, term, category,location,url) 
VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'''
    with con:
        cur.executemany(sql, insert_data)
        
        
        
def prompt_search():
    '''
    prompt the user to input the information about the restaurants they want to search for.
    If the returned items from API request are not stored in cache, they will be stored in the cache. Besides, they will also be stored in the database.
    SQL queries are used to extract information from the database.
    Based on the extracted information from the database, users are prompted to choose from the visualization options.
    
    Parameters
    ----------
    none
    
    Returns
    -------
    DataFrame:
        the dataframe which include the information of all the recommended restaurants.
    '''
    user_term = input(
        '''What restaurants do you want to find? You can input the type of dishes(e.g. hotpot, seafood), the name of restaurant(e.g. Macdonald), or the style of cooking(Chinese,Italian).  '''
    )
 
    rough_location = input(
        '''Around which location do you want to search for restaurants? You can just input "New York City" or any specific address like "350 5th Ave, New York, NY 10118". However, the recommendations you get from our system may not be strictly within the specified location.  '''

    )
    while True:
        number_of_recommendation= input('''How many recommended restaurants do you want to have? Please input a number from 1 to 20.  ''')
        if number_of_recommendation.isdigit() and (int(number_of_recommendation)>=1 and int(number_of_recommendation)<=20):
            number_of_recommendation=int(number_of_recommendation)
            break
        else:
            print('''invalid input of "number of recommendation", please input again.  ''')
    
    url='https://api.yelp.com/v3/businesses/search?'
    params= {'term':user_term,'location':rough_location, 'category':'restaurants','attributes':'open_to_all', 'sort_by':'rating', 'limit':20}
    input_db, cache_current=make_url_request_use_cache(url,CACHE_DICT,params=params,headers=HEADER,merchant_id='none')
    if input_db==False:
        write_into_merchant(params['term'],params['category'],params['location'],cache_current)
    else:
        pass
    sql='''select * from merchant where term=? and category=? and location=? order by score desc limit ?'''
    cur.execute(sql, (params['term'],params['category'],params['location'], number_of_recommendation))
    res = cur.fetchall()
    recommendation_id=[]
    recommendation_name=[]
    recommendation_address=[]
    recommendation_latitude=[]
    recommendation_longitude=[]
    recommendation_phone=[]
    recommendation_url=[]
    recommendation_score=[]
    for line in res:
        recommendation_id.append(line[0])
        recommendation_name.append(line[1])
        recommendation_address.append(line[2])
        recommendation_latitude.append(line[3])
        recommendation_longitude.append(line[4])
        recommendation_phone.append(line[5])
        recommendation_score.append(line[8])
        recommendation_url.append(line[12])
    recommendation_table=pd.DataFrame({'id':recommendation_id,
                                       'name':recommendation_name,
                                       'address':recommendation_address,
                                       'phone':recommendation_phone,
                                       'latitude':recommendation_latitude,
                                       'longitude':recommendation_longitude,
                                       'score':recommendation_score,
                                       'url':recommendation_url,
                                      })
    for i in range(len(recommendation_table)):
        input_menu_and_comment(recommendation_table['id'][i],recommendation_table['url'][i])
    while True:
        visualization=input('''which visualization do you like? A bar plot, a scatter plot, a map plot or a table? A bar plot and a scatter plot clearly show the scores of each recommended restaurant. A map plot clearly show the location of each restaurant. A table show the information of each recommendation in an ordered way. Please input "bar" or "scatter" or "map" or "table".''')
        if (visualization=='map' ):
            plot_map(recommendation_table)
            print('By hovering on the point, you can see the id, name, address, phone, score of each recommended restaurant.')
            break
        elif (visualization=='bar' ):
            plot_bar(recommendation_table)
            print('By hovering on the bar, you can see the id, name, address, phone, score of each recommended restaurant.')
            break
        elif( visualization=='table'):
            plot_table(recommendation_table)
            break
        elif( visualization=='scatter'):
            plot_scatter(recommendation_table)
            print('By hovering on the point, you can see the id, name, address, phone, score of each recommended restaurant.')
            break
        else:
            print("Invalid Input. Please input again")
        
    return recommendation_table



if __name__ == "__main__":
    CACHE_DICT=load_cache()
    print(
        '''Hi, welcome to our recommendation system. Our system provides recommendations for restaurants in New York City.'''
    )
    
        
    recommendation_table=prompt_search()   
    
    while True:
        look_at_menu_and_review=input('''If you are interested in any of the restaurant and want to look at its menu and reviews, please input the id of it.\nIf you want to see another kind of visualization, please input the name of it('bar','scatter','table','map').\n If you want to exit, please enter "exit".\n If you want to start another search, please enter "back".''')
        if look_at_menu_and_review.isdigit() and int(look_at_menu_and_review) in recommendation_table['id'].tolist():
            sql='''select * from menu where merchant_id= ?'''
            cur.execute(sql, (look_at_menu_and_review,))
            res = cur.fetchall()
            all_menu_display=[]
            for i in res:
                all_menu_display.append(i[2])
            sql='''select * from review where merchant_id= ?'''
            cur.execute(sql,(look_at_menu_and_review,))
            res = cur.fetchall()
            all_review_display=[]
            for i in res:
                all_review_display.append(i[2])
            print_menu_and_reviews(recommendation_table[recommendation_table['id']==int(look_at_menu_and_review)]['name'].tolist()[0],   all_menu_display,all_review_display)
        elif (look_at_menu_and_review=='exit'):
            print('exiting')
            sys.exit(0)
        elif(look_at_menu_and_review=='back'):
            recommendation_table=prompt_search()
        elif(look_at_menu_and_review=='bar'):
            plot_bar(recommendation_table)
            print('By hovering on the bar, you can see the id, name, address, phone, score of each recommended restaurant.')
        elif(look_at_menu_and_review=='scatter'):
            plot_scatter(recommendation_table)
            print('By hovering on the scatter, you can see the id, name, address, phone, score of each recommended restaurant.')
        elif(look_at_menu_and_review=='map'):
            plot_map(recommendation_table)
            print('By hovering on the point, you can see the id, name, address, phone, score of each recommended restaurant.')
        elif(look_at_menu_and_review=='table'):
            plot_table(recommendation_table)
        else:
            print('Invalid input. Please input again.')  
        
    


        
    
    
            
    
    