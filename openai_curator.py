import pathlib
import json
import os
import json
import ast
import requests
from datetime import datetime, timedelta
from openai import OpenAI
client = OpenAI()

cwd = pathlib.Path(__file__).parent.resolve()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
	raise Exception("You need to get an API key from OpenAI (https://platform.openai.com/api-keys) and store it as your system environment variable, naming it OPENAI_API_KEY")

SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
	raise Exception("You need to get an API key from SerpAPI (https://serpapi.com/manage-api-key) and store it as your system environment variable, naming it SERPAPI_API_KEY")

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
	id = 1
	for result in results["news_results"]:
		# some parameters may not be in the source, so skip those articles if they don't exist
		source = result["source"]
		if ("name" in source) and ("icon" in source) and ("link" in result) and ("thumbnail" in result) and ("date" in result):
			
			date = format_date(result["date"])
			result_dict = {
				"id":id,
				"title":result["title"],
				"site_name":source["name"],
				"site_icon":source["icon"],
				"link":result["link"],
				"thumbnail":result["thumbnail"],
				"date":date
			}
			results_list.append(result_dict)
			id += 1

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
		titles.append({"id":result["id"], "article":result["title"]})

	query = f"Cybersecurity incidents or announcements that are important for a company from {country} in the {sector} sector as well as major global news."

	completion = client.chat.completions.create(
		model="gpt-4o",
		response_format={"type":"json_object"},
		messages=[
			{"role": "system", "content": "You are an assistant that helps filter and summarize news articles based on a user query."},
			{"role": "user", "content": f"The news articles are: {titles}. The query is: {query}."},
			{"role": "user", "content": f"""Your task is to:
		- Select the {num_of_articles} most relevant article titles to the query from the list.
		- If multiple articles cover the same story, pick only one of them.
		- Store the id of selected titles in a Python array.The ids should be written as integers, not strings.
		- Write a summary of less than 150 words that allows a reader to understand all the events covered by the selected {num_of_articles} articles in a short paragraph.

		Return the result in the following JSON-like format without any extra text:
		{{"articles": <array of selected article ids>, "summary": <summary of the selected articles>}}
		
		Example response:
		{{"articles": [4, 6, 7], "summary":Google was hit by a cyber attack with no one claiming responsibility yet. CSA has announced new rules and regulations for organisations to abide by. A data breach has exposed peresonal data in India.}}
		"""
			}
		]
	)

	response_str = completion.choices[0].message.content
	print(response_str)

	try:
		response_json = ast.literal_eval(response_str)
		articles = response_json["articles"]
		summary = response_json["summary"]
	except Exception:
		raise Exception(f"\nError when parsing GPT's response. Try running the script again. The response should be in a dictionary as such: {{'articles':<array of articles>, 'summary':<paragraph>}}\nThe received response was: \n{response_str}")
	
	with open(f"{cwd}\\data\\all_{country}_news.json", "r") as f:
		all_news_strings = f.read()
		all_news = json.loads(all_news_strings)
		filtered_news = {"articles":[entry for entry in all_news if entry["id"] in articles],"summary":summary}

	return filtered_news 

def format_date(date):
	# Modify the date string to remove the ' UTC' part
	date_str = date.replace(' UTC', '')

	# Parse the original string into a datetime object
	date_obj = datetime.strptime(date_str, '%m/%d/%Y, %H:%M %p, %z')

	# Convert the time to Singapore time (UTC+08:00)
	singapore_offset = timedelta(hours=8)
	singapore_time = date_obj + singapore_offset

	# Format the date as dd/mm/yyyy, HH:MM AM/PM
	formatted_date = singapore_time.strftime('%d/%m/%Y, %I:%M %p')

	return formatted_date

# Retrieve all Singapore and Malaysia news using SerpAPI
countries = ["singapore", "malaysia"]
for country in countries:
	all_news = retrieve_news(country)
	with open(f"{cwd}\\data\\all_{country}_news.json", "w") as f:
		json.dump(all_news, f)

	# Filter news using Gemini AI
	sectors = ["finance", "it", "nonprofit", "food_and_beverage", "media"]
	for sector in sectors:
		filtered_news = filter_news(country, sector, 8)
		with open(f"{cwd}\\data\\{country}_{sector}.json", "w") as f:
			json.dump(filtered_news, f)