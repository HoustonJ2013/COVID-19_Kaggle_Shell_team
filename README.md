# COVID-19_Kaggle_Shell_team

## Meeting notes
### 1. 3/22/2020
(1) determine work on task 2 about "ideintifying risk factors"  
(2) Elastic search, identify papers and paragraph.  
(3) Q&A application. github available. (https://towardsdatascience.com/nlp-building-a-question-answering-model-ed0529a68c54)  
(4) Risk factor, key word identification, summarize case distribution.  
(5) Use reference to group articles and identify closely related "community".  

Task:  
(1) Jenny - identify risk factor - related words (read paper, online translator, find synonyms), or medical tools  
(2) Jingbo - investigate elastic search.  
(3) Yinsen - graphic analysis. paper reference  
(4) Tina - NLP  

### 2. 3/29/2020
Proposed strategy:  
(1) reference-based clustering map. Identify each cluster. "topic" modeling. - Yinsen  
(2) elastic search, identify papers by key words. Provide pickle file with "selected paragraph". - Jingbo  
(3) key words related paper, table statistics summary. - Jenny  
(4) NLP-based statistics, Gensim. - Tina  
NER return location of key words. BM25. (Gensim,cTAKES, MetaMap)  

=======
### 3. 4/4/2020
(1) Jenny introduced her notebook results, with submission draft format  
(2) Jingbo introduced his code udpates: update database, update searching query (support multiple words searching)  
(3) Tina introduced her her code about BM25, nltk. (available in github?)  
(4) Yinsen introduced the software used to visualize community network. Pubmed ID? jason file?

Proposed workflow:
1. Elastic search + pre-calculated community belongings.   
2. With given "paper_id", provide related sentences.  

(0) Yinsen, save community number out for paper. - visualization.   
(1) combine elastic search results with Yinsen's calculated community. => top papers   
(2) For "selected papers", keep searching "paragraph" from top papers.   
  
Task: (1) input question, output keywords - Tina  
      (2) input keywords + one paper, output top three sentences  - jingbo  
      (3) interface. Input question, output sentences. - Jenny  


############### Elastic Search Setup #######################

1. Have a sever on the cloud with minimum mem 16 GB, and 128 GB disk space. The server has to be have static IP address, and docker, python isntalled

2. open a terminal on the server, and run the command
```
source docker_elastic_setup.rsc
```
Now the server is set up 

3. Clone this repo to the cloud server, modify the folder path to the json files in the script, and run the script. Note install whatever package missing on the cloud server (ideally we should us docker for more serious deployment)
```
python elasticsearch_helpers.py
```

4. Please refer to 0408_elasticsearch_Query_example.ipynb for keywords and keyphrases query