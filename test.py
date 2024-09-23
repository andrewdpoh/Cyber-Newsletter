from openai import OpenAI
client = OpenAI()

country = "singapore"
sector = "structures"
titles = ["steve jobs", "eiffel tower", "waterfalls", "crowdstrike power outage", "drone attack in iraq"]
num_of_articles = 2

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
	- Store the selected titles in a Python array.
	- Write a summary that allows a reader to understand all the events covered by the selected {num_of_articles} articles in a short paragraph.

	Return the result in the following JSON-like format without any extra text:
	{{"articles": <array of selected articles>, "summary": <summary of the selected articles>}}"""
		}
	]
)

print(type(completion.choices[0].message.content))