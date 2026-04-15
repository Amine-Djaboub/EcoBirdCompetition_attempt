import wikipedia

def fetch_species_info(species_name):
    """Smartly queries Wikipedia using search algorithms to find the right bird."""
    try:
        # We append "bird" to the search so Wikipedia doesn't give us a sports team or movie!
        query = f"{species_name} bird"
        
        # 1. Search Wikipedia for the closest matches
        search_results = wikipedia.search(query)
        
        if not search_results:
            return {
                "Status": "Information not found in database.",
                "Suggestion": "Try checking eBird for localized data."
            }
            
        # 2. Grab the actual page for the top search result
        best_match = search_results[0]
        page = wikipedia.page(best_match, auto_suggest=False)
        
        # 3. Extract a clean, short summary
        summary = page.summary.split('\n')[0] # Grab just the first paragraph
        if len(summary) > 400:
            summary = summary[:397] + "..."
            
        return {
            "Wikipedia Match": page.title,
            "Overview": summary,
            "Source URL": page.url
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        # If Wikipedia is confused (e.g., multiple birds with similar names), grab the first option
        try:
            page = wikipedia.page(e.options[0], auto_suggest=False)
            return {
                "Wikipedia Match": page.title,
                "Overview": page.summary.split('\n')[0][:397] + "...",
                "Source URL": page.url
            }
        except:
            return {"Error": "Too many similar species found."}
            
    except Exception as e:
        return {"Error": "Connection failed or Wikipedia is down."}