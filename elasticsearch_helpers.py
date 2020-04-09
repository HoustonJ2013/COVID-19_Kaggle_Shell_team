import logging
from elasticsearch import Elasticsearch, helpers
import pandas as pd
import sys, json
import os
from tqdm import tqdm

######################## Global tables and folder path ###############################

ES_HOST = "localhost" ## Change to the cloud server IP address

################ Modify the path to the meta data ####################################
metadata_df = pd.read_csv("../data/2020-04-03/metadata.csv") ## Modify path to metadata here
metadata_df.set_index("sha", inplace=True)
metadata_df["publish_year"] = metadata_df["publish_time"].apply(lambda x: str(x).split("-")[0] if "-" in str(x) else str(x).split()[0])
metadata_df["publish_year"] = metadata_df["publish_year"].apply(lambda x: x.split()[0])
metadata_df["publish_year"] = metadata_df["publish_year"].apply(lambda x: x.split()[0].replace("['", ""))
metadata_df["publish_year"] = metadata_df["publish_year"].fillna(-1)
metadata_df.loc[metadata_df["publish_year"] == "nan", "publish_year"] = "-1"


##  Modify the folder paths if updated 
directory1_pdf = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/biorxiv_medrxiv/biorxiv_medrxiv/pdf_json/"
directory1_pmc = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/biorxiv_medrxiv/biorxiv_medrxiv/pmc_json/"
directory2_pdf = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/comm_use_subset/comm_use_subset/pdf_json/"
directory2_pmc = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/comm_use_subset/comm_use_subset/pmc_json/"
directory3_pdf = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/custom_license/custom_license/pdf_json/"
directory3_pmc = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/custom_license/custom_license/pmc_json/"
directory4_pdf = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/noncomm_use_subset/noncomm_use_subset/pdf_json/"
directory4_pmc = "/media/jingbo/1TB_disk/01_Projects/03_Competition/11_kaggle_Projects/11_covid-19/data/2020-04-03/noncomm_use_subset/noncomm_use_subset/pmc_json/"
all_json_files = []
all_json_files += [directory1_pdf + tem_ for tem_ in os.listdir(directory1_pdf) if tem_.endswith(".json")]
# list_files += [directory1_pmc + tem_ for tem_ in os.listdir(directory1_pmc) if tem_.endswith(".json")]

all_json_files += [directory2_pdf + tem_ for tem_ in os.listdir(directory2_pdf) if tem_.endswith(".json")]
all_json_files += [directory2_pmc + tem_ for tem_ in os.listdir(directory2_pmc) if tem_.endswith(".json")]

all_json_files += [directory3_pdf + tem_ for tem_ in os.listdir(directory3_pdf) if tem_.endswith(".json")]
all_json_files += [directory3_pmc + tem_ for tem_ in os.listdir(directory3_pmc) if tem_.endswith(".json")]

all_json_files += [directory4_pdf + tem_ for tem_ in os.listdir(directory4_pdf) if tem_.endswith(".json")]
all_json_files += [directory4_pmc + tem_ for tem_ in os.listdir(directory4_pmc) if tem_.endswith(".json")]

print("There are %i of json files"%(len(all_json_files)))
#######################################################################################
## Helper functions
## crease index with the limit of total fields 30000
def create_index(es_object, index_name='recipes', num_total_fields=3000):
    created = False
    # index settings
    settings = {
        "settings": {
            "index.mapping.total_fields.limit": num_total_fields,
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }
    try:
        if not es_object.indices.exists(index_name):
            es_object.indices.create(index=index_name, body=settings)
            print('Created Index', index_name)
            created = True
        else:
            print(index_name, "already exist!!")
        
    except Exception as ex:
        print(str(ex))
    finally:
        return created
## Load single json
def store_record(elastic_object, index_name, doc_type, id, json_record):
    try:
        outcome = elastic_object.index(index=index_name, doc_type=doc_type, id=id, body=json_record)
    except Exception as ex:
        print("Error for index", index_name)
        print(str(ex))
        

def store_bulk(elastic_object, index_name, doc_type, json_list, timeout=100):
    try:
        outcome = helpers.bulk(elastic_object, 
                               json_list, 
                               index=index_name, 
                               doc_type=doc_type, 
                               request_timeout=timeout)
    except Exception as ex:  
        print("Error loading batch")


## batch load json files
def batch_json_record(file_list, batch_size=16):
    n_file = len(file_list)
    n_batch = int(n_file / batch_size) if n_file % batch_size==0 else int(n_file / batch_size) + 1
    for i in range(n_batch):
        batch_file_list = file_list[i * batch_size : (i + 1) * batch_size]
        json_list = []
        for json_file_ in batch_file_list:
            with open(json_file_, "r") as open_file:
                data_ = json.load(open_file)
            paper_id = json_file_.split("/")[-1].replace(".json", "")
            if paper_id in metadata_df.index:
#                 data_["publish_time"] = metadata_df.loc[paper_id]["publish_time"]
                data_["publish_year"] = metadata_df.loc[paper_id]["publish_year"]
            else:
#                 data_["publish_time"] = "-1"
                data_["publish_year"] = "-1"
            data_["_id"] = paper_id
            json_list.append(data_)
        yield json_list


#### Helper functions for query 
def es_extract(hits):
    scores = []
    paper_ids = []
    publish_years = []
    titles = []
    abstracts = []
    sources = []
    for hit in hits:
        scores.append(hit["_score"])
        paper_ids.append(hit["_source"]["paper_id"])
        publish_years.append(hit["_source"]["publish_year"])
        titles.append(hit["_source"]["metadata"]["title"])
        if "abstract" in hit["_source"]:
            abstracts.append(" ".join([tem_["text"] for tem_ in hit["_source"]["abstract"]]))
        else:
            abstracts.append([])
        sources.append(hit["_source"])

    return scores, paper_ids, publish_years, titles, abstracts, sources 


def es_equery(es, query, index='covid-kaggle', doc_type="pdf_json"):
    '''
    accept : es connection and query doc
    return : dataframe with paper_id, match_scores, publish_year, titles, abstracts, json_contents
    '''
    res3 = es.search(index=index, doc_type=doc_type, body=query, size=200)
    print("There are %i of papers returned"%(res3["hits"]["total"]["value"]))
    
    scores, paper_ids, publish_years, titles, abstracts, sources  = es_extract(res3["hits"]["hits"])
    df_return = pd.DataFrame.from_dict({
        "paper_id": paper_ids, 
        "match_scores": scores, 
        "publish_years": publish_years, 
        "title": titles, 
        "abstract": abstracts, 
        "json_obj": sources
    })
    return df_return


def query_key_words_phrases(keywords, keyphrases, task="risk factor"):
    
    multi_match = []
    
    ## task 
    if len(task) > 0:
        multi_match.append(
         {"multi_match": {
                "query": task, 
                "type": "phrase", 
                "fields": ["metadata.title", "abstract.text", "body_text.text"]}},  
        )
    
    ## keywords
    
    if len(keywords) > 0:
        for keyword in keywords:
            multi_match.append(
             {"multi_match": {
                "query": keyword, 
                "type": "cross_fields", 
                "fields": ["metadata.title", "abstract.text", "body_text.text"]}},  
            )
    
    if len(keyphrases)> 0:
        for keyphrase in keyphrases:
            multi_match.append(
             {"multi_match": {
                "query": keyphrase, 
                "type": "phrase", 
                "fields": ["body_text.text", "abstract.text"]}},  
            )

        
    covid_topic_match = []
    
    covid_key_words = ["novel coronavirus", 
                       "covid-19", 
                       "2019-nCoV", 
                       "novel CoV", 
                       "SARS Coronavirus 2", 
                       "SARS-CoV-2"
                      ]
    for covid_key_word in covid_key_words:
#         covid_topic_match.append(
#         {"match_phrase": {"metadata.title":covid_key_word}}
#         )
        covid_topic_match.append(
            {"multi_match": {
                "query":covid_key_word, 
                "type" : "phrase", 
                "fields": ["metadata.title", "abstract.text"]
            }
            }
        )
        
    
    query = {
            'query': {
                "bool":{
                    "must":
                       [
                         multi_match
                        ], 

                    "should":  ## For Convid-19 big topic
                    [  
                      covid_topic_match
                    ], 
                    "minimum_should_match" : 1,
                }
            }
       }
    return query



def main():
    index_name = "covid-kaggle"
    doc_type = "pdf_json"
    es = Elasticsearch(hosts=[{"host":ES_HOST, "port":9200}], request_timeout=12000) ## Make connection
    ## Create index if not done yet
    create_index(es, index_name=index_name, num_total_fields=50000) ## Increase the num_total_fields of fields if a significant amout of jsons are not loaded


    ## Check how many papers are already loaded 
    ## Check how many jsons load successfully 
    ## Query to get all ids
    query = { 
        'size' : 10000,
        "query" : { 
            "match_all" : {} 
        },
        "stored_fields": []
    }
    a=helpers.scan(es,query=query,scroll='1m',index='covid-kaggle')#like others so far
    all_es_ids=[aa['_id'] for aa in a]
    print("There are %i of ids loaded in current index and doc type"%(len(all_es_ids)))

    all_paper_ids = [json_file_.split("/")[-1].replace(".json", "") for json_file_ in all_json_files]
    missed_ids = set(all_paper_ids) - set(all_es_ids)
    missed_file_list = [tem_[0] for tem_ in zip(all_json_files, all_paper_ids) if tem_[1] in missed_ids]
    print("There are %i of ids not inserted successuflly"%(len(missed_file_list)))


    batch_size = 8
    n_batches = len(all_json_files) / batch_size + 1
    i = 0
    for json_list in batch_json_record(missed_file_list, batch_size=batch_size):
        i += 1
        if i%100 == 99:
            print("%i/%i done"%(i, n_batches))
        store_bulk(es, index_name, doc_type, json_list)


    ## Check how many jsons load successfully 
    ## Query to get all ids
    query = { 
        'size' : 10000,
        "query" : { 
            "match_all" : {} 
        },
        "stored_fields": []
    }
    a=helpers.scan(es,query=query,scroll='1m',index='covid-kaggle')#like others so far
    all_es_ids=[aa['_id'] for aa in a]
    print("There are %i of ids loaded in current index and doc type"%(len(all_es_ids)))

    all_paper_ids = [json_file_.split("/")[-1].replace(".json", "") for json_file_ in all_json_files]
    missed_ids = set(all_paper_ids) - set(all_es_ids)
    missed_file_list = [tem_[0] for tem_ in zip(all_json_files, all_paper_ids) if tem_[1] in missed_ids]
    print("There are %i of ids not inserted successuflly"%(len(missed_file_list)))

    pass

if __name__ == "__main__":
    main()