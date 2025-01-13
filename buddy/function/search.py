import os
import requests
from xml.etree import ElementTree as ET

def search_arxiv(query, max_results=8):
    url = 'http://export.arxiv.org/api/querys'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return f"Error: Unable to fetch data from arXiv (Status code: {res.status_code})"

    root = ET.fromstring(res.content)
    output = ""
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in
                   entry.findall('{http://www.w3.org/2005/Atom}author')]

        output += f"""
        Title: {title.strip()}
        Summary: {summary.strip()}
        Link: {link.strip()}
        Published: {published.strip()}
        Authors: {authors}
        """
    return output
