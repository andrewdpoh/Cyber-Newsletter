import pathlib
import json
import os
import google.generativeai as genai
import json
import ast
import requests

cwd = pathlib.Path(__file__).parent.resolve()

# You need to get an Google API key from the Gemini website and store it as your system environment variable called GOOGLE_API_KEY
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
	raise Exception("You need to get an Google API key from Google (https://aistudio.google.com/app/apikey) and store it as your system environment variable, naming it GOOGLE_API_KEY")

SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
	raise Exception("You need to get an SerpAPI API key from SerpAPI (https://serpapi.com/manage-api-key) and store it as your system environment variable, naming it SERPAPI_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def retrieve_news(country):
	"""Retrieves cyber-related news based on country (singapore or malaysia)

	Args:
		keywords (list): keywords for the query
		country (str): either "singapore" or "malaysia"

	Returns:
		list: a list of results where each result is a dictionary
	"""

	if country == "singapore":
		country = "SG"
	elif country == "malaysia":
		country = "MY"
	else:
		raise Exception("Country input is wrong. It should only be either 'singapore' or 'malaysia'")

	url = "https://serpapi.com/search"
	params = {
		"engine": "google_news", # use google_news search
		"api_key": SERPAPI_API_KEY, # put in your own api key from SerpAPI
		"q": "cyber when:1d", # query | when:1d filters for results in the past day
		"gl": country, # localization: SG or MY
		# "hl":"en", # language: english
	}

	response = requests.get(url, params=params)
	results = response.json()

	results_list = []
	for result in results["news_results"]:
		# some parameters may not be in the source, so skip those articles if they don't exist
		source = result["source"]
		if ("name" in source) and ("icon" in source) and ("link" in result) and ("thumbnail" in result):

			# check if all links and titles are less than 200 characters, else they won't fit in the SQL database
			# if (len(source["name"]) < 200) and (len(source["icon"]) < 200) and (len(result["link"]) < 200) and (len(result["thumbnail"]) < 200):
			if source["name"] and source["icon"] and result["link"] and result["thumbnail"] and result["date"]:
				result_dict = {
					"title":result["title"],
					"site_name":source["name"],
					"site_icon":source["icon"],
					"link":result["link"],
					"thumbnail":result["thumbnail"],
					"date":result["date"]
				}
				results_list.append(result_dict)

			else:
				pass
		else:
			pass
	
	return results_list

def filter_news(country, sector, num_of_articles):
	"""Filters for news based on the company's sector

	Args:
		sector (str): Sector of the company
		num_of_articles (int): Number of filtered articles
		country (str): Country of the company
	"""	
	
	# Retrieve the list of all the articles
	with open (f"{cwd}\\data\\all_{country}_news.json","r") as f:
		results = f.read()
		results = json.loads(results)

	# Compile all article titles into a list
	titles = []
	for result in results:
		titles.append(result["title"])

	query = f"Cybersecurity incidents or announcements that are important for a company from {country} in the {sector} sector as well as major global news that is repeated many times in the list of titles."

	prompt = f"""
You are given this array of news article titles" {titles}. 
Based on the query '{query}', select the {num_of_articles} most relevant news articles from the array. 
If multiple articles seem to cover the same news, only pick 1 of the articles.
Your reply should exactly match the format of an array of the articles titles you have picked like such: ['title1','title2','title3']. 
Ensure the article titles are copied correctly and the JSON format is correct. Please escape any characters that should be escaped in the titles such as aprostrophes.
The reply should not contain any extra characters like backticks or words outside of the array.
"""

	response = model.generate_content(prompt)
	# print("Gemini's response:", response.text)
	# print(f"Gemini's response type: {type(response.text)}")
	try:
		titles = ast.literal_eval(response.text)
	except Exception:
		raise Exception(f"\nError when parsing Gemini's response. Try running the script again. The response should be in a list such as ['title1', 'title2']\nGemini's response was: \n{response.text}")
	
	with open(f"{cwd}\\data\\all_{country}_news.json", "r") as f:
		all_news_strings = f.read()
		all_news = json.loads(all_news_strings)
		filtered_news = [entry for entry in all_news if entry["title"] in titles]

	return filtered_news 

# Retrieve all Singapore and Malaysia news using SerpAPI
countries = ["singapore", "malaysia"]
for country in countries:
	all_news = retrieve_news(country)
	with open(f"{cwd}\\data\\all_{country}_news.json", "w") as f:
		json.dump(all_news, f)

	# Filter news using Gemini AI
	sectors = ["finance", "it"]
	for sector in sectors:
		filtered_news = filter_news(country, sector, 8)
		with open(f"{cwd}\\data\\{country}_{sector}.json", "w") as f:
			json.dump(filtered_news, f)