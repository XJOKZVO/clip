# clip
Tool This code is a web crawler implemented in Python using the BeautifulSoup library to parse HTML and the Requests library to make HTTP requests. It is quite comprehensive, covering different types of resources such as links, scripts, forms, images, etc., and can crawl multiple pages simultaneously using ThreadPoolExecutor.

# Installation
```
https://github.com/XJOKZVO/clip.git
cd clip
pip install -r requirements.txt
python clip.py
```

# Options:
```
           ***                        
            ***      *                
             **     ***               
             **      *                
             **               ****    
   ****      **    ***       * ***  * 
  * ***  *   **     ***     *   ****  
 *   ****    **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
**           **      **    **    **   
***     *    **      **    *******    
 *******     *** *   *** * ******     
  *****       ***     ***  **         
                           **         
                           **         
                            **        

usage: clip.py [-h] [-i] [-d DEPTH] [-s] [-w] [-j] [--headers HEADERS] [urls ...]

Web crawler

positional arguments:
  urls                  URLs to crawl

options:
  -h, --help            show this help message and exit
  -i, --inside          Only crawl inside path
  -d DEPTH, --depth DEPTH
                        Depth to crawl
  -s, --show-source     Show the source of URL
  -w, --show-where      Show where the URL is found
  -j, --show-json       Output as JSON
  --headers HEADERS     Custom headers separated by two semi-colons
```

# Usage:
```
python clip.py https://example.com -s
python clip.py https://example.com -i
python clip.py https://example.com -d 2
python clip.py https://example.com -w
python clip.py https://example.com -j
python clip.py https://example.com --headers "User-Agent: MyCustomUserAgent;;Authorization: Bearer myToken"
```
