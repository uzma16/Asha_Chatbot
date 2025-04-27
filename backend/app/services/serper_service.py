import aiohttp
import json
import os
import cachetools
import logging

logger = logging.getLogger(__name__)
cache = cachetools.TTLCache(maxsize=100, ttl=3600)

async def search_serper(query: str) -> str:
    cache_key = f"serper_{query}"
    if cache_key in cache:
        return cache[cache_key]
    
    top_result_to_return = 4
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": os.environ.get('SERPER_API_KEY', 'YOUR_SERPER_API_KEY'),
        "Content-Type": "application/json"
    }
    payload = json.dumps({"q": query, "num": top_result_to_return})
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Serper API response: {json.dumps(data, indent=2)}")
                    if 'organic' not in data:
                        result = "Sorry, I couldn't find anything about that. There may be an issue with the Serper API key."
                    else:
                        results = data['organic']
                        string = []
                        for result in results[:top_result_to_return]:
                            try:
                                string.append('\n'.join([
                                    f"Title: {result['title']}",
                                    f"Link: {result['link']}",
                                    f"Snippet: {result['snippet']}",
                                    "\n-----------------"
                                ]))
                            except KeyError:
                                continue
                        result = '\n'.join(string) if string else "No recent updates found."
                    cache[cache_key] = result
                    return result
                else:
                    logger.error(f"API error: {response.status}")
                    return f"API error: {response.status}"
    except Exception as e:
        logger.error(f"Error searching Serper: {str(e)}")
        return "Unable to fetch updates at this time."