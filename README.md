## Vaporpic - Vidnode API for Originating Pirated Content
***

*This module is intended to be used as an API, but it can also can be run standalone to fetch TV shows and movies.
The documentation of it's installation and usage both as an API and a standalone module is below:*

***
## Installation
***
This module can be installed using the provided requirements.txt.

**Windows**

Run the following command to install the required modules:

```
python -m pip install -r requirements.txt
```

**Ubuntu/Debian Linux**

Run the following command to install the required modules:

```
python3 -m pip install -r requirements.txt
```
***
## Standalone Usage
***

*To use the module in standalone mode, after installing the required modules from the requirements.txt, run the 
following in a terminal (this is assuming you're in the directory where you cloned the repo):*

**Windows**
```
python vaporpic.py
```

**Ubuntu/Debian Linux**
```
python3 vaporpic.py
```
You will be greeted with the following prompt:
```
Select media type:

1. Movie

2. TV

```
If you select a movie, you will then be prompted with the following:
```
Title:
```
After entering the title, if links are found, you will either immediately get the link and quality back, or you will
be prompted to select a quality like this:

```
Available Qualities:

0. Original

1. 720p

2. 480p

```

After selecting the quality, you will then receive the link, which looks like this:

```
Link:

https://st3.cdnfile.info/user592/8bf990046e57663ede3679042ed44995/EP.1.mp4?token=QckhmxMyO9rUvcUMFeCxSQ&expires=1574909154&title=(orginalP - mp4) Remember+The+Titans+HD-720p
```

*This process is exactly the same for TV, with the only difference being you will also be prompted for
season and episode numbers.*
***
## API Usage
***
**Classes:**

* VidnodeApi(media_type, title, ***kwargs) -> VidnodeApi object
    * **Arguments:**
        * *media_type (str)* -> "movie" or "tvod" (this class can do both movies and TV)
        
        * *title (str)* -> The title of the requested media
        
        * ***kwargs (str)* -> Keyword arguments for season and episode when media_type is tvod.
            "s" is passed to denote the season and "e" is passed to denote the 
            episode
    
    * **Examples:**
        ```
         va = VidnodeApi("movie", "Star Wars: The Force Awakens")
        ```
        ```
         va = VidnodeApi("tvod", "Breaking Bad", s="4", e="1")
        ```

    **Methods:**
        
     * *assemble_search_url()* -> assembled search url (str) 
     
       **note: if the string returned by this method is empty, the 
       title is not available from the source this class scrapes**
       
     * *assemble_media_url(search_url)* -> assembled media url (str) 
       
       * **Arguments:**
          
          * *search_url (str)* -> the search url returned by the *assemble_search_url* 
            method
            
     * *scrape_final_links(media_url, bot_mode)* -> dict object with links and qualities if available
       
       * **Arguments:**
       
         * *media_url (str)* -> the media url returned by the *assemble_media_url* method  
         
         * *bot_mode (boolean)* -> Whether or not this is being used in the contexr of a reddit bot. This determines
           whether the raw mp4 links should be returned, or just a link to the download page
           
           **note: The *bot_mode* arg is required because the raw mp4 links craft IP based tokens for the person who 
           requests them, therefore they would only be valid for the person who made the request
           and wouldn't work in the context of a link scraping/sharing bot.** 
      
       * **Examples:**
       
         ```
          from vaporpic import *
         
          va = VidnodeApi("tvod", "Breaking Bad", s="4", e="1")
          search_url = va.assemble_search_url()
          media_url = va.assemble_media_url(search_url)
          link_dict = va.scrape_final_links(media_url, False)
          print(link_dict)
          
         [out]>> {'browser_link': 'https://vidnode.net/streaming.php?id=NDY0NzE=&title=Breaking+Bad+-+Season+4+Episode+01%3A+Box+Cutter&typesub=SUB&sub=L2JyZWFraW5nLWJhZC1zZWFzb24tNC1lcGlzb2RlLTAxLWJveC1jdXR0ZXIvYnJlYWtpbmctYmFkLXNlYXNvbi00LWVwaXNvZGUtMDEtYm94LWN1dHRlci52dHQ=&cover=L2JyZWFraW5nLWJhZC1zZWFzb24tNC1sd2cvY292ZXIucG5n', 
                  'hotlinks': {'Original': 'https://st3.cdnfile.info/user592/d8ced999b2b4edc18f3fb6067f05c0c4/EP.1.mp4?token=SRJPBblJ2w9U-gQ-lmxprg&expires=1574913655&title=(orginalP - mp4) Breaking+Bad+-+Season+4+Episode+01%3A+Box+Cutter'}}
         ```  
        