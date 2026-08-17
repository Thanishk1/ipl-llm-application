ABBREV_MAP = {
    "SRH": "Sunrisers Hyderabad",
    "GT": "Gujarat Titans",
    "LSG": "Lucknow Super Giants",
    "CSK": "Chennai Super Kings",
    "KKR": "Kolkata Knight Riders",
    "RCB": "Royal Challengers Bengaluru",
    "MI": "Mumbai Indians",
    "RR": "Rajasthan Royals",
    "PBKS": "Punjab Kings",
    "DC": "Delhi Capitals",
}

def expand_query(query, abbrev_map=ABBREV_MAP):
    # your code: for each abbreviation found in query, APPEND the full name
    # (not replace) so both forms are present in the text that gets embedded
    words = query.split()
    for w in words:
        if w.upper() in abbrev_map.keys():
            query+= " "+abbrev_map[w.upper()]
    return query 
